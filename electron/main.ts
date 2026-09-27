import { app, BrowserWindow, shell, utilityProcess, type UtilityProcess } from "electron";
import path from "node:path";
import fs from "node:fs";
import net from "node:net";
import http from "node:http";

/**
 * Electron main process for the MERAGLYM desktop app.
 *
 * It runs the Next.js standalone server as a Node utility process (Electron
 * bundles its own Node runtime, so nothing extra is required on the user's PC),
 * waits for it to become ready on a local port, then displays it in a window.
 * The app uses the embedded SQLite database (MERAGLYM_DB_MODE=local); the
 * database file lives in the user's writable app-data directory and is seeded
 * on first launch from the read-only copy shipped in the installer.
 */

const isDev = !app.isPackaged;

// Root that contains `.next/standalone` and (in dev) `resources/`.
function appRoot(): string {
  return isDev ? process.cwd() : app.getAppPath();
}

function standaloneServerPath(): string {
  return path.join(appRoot(), ".next", "standalone", "server.js");
}

function seedDbPath(): string {
  // Packaged: shipped via electron-builder extraResources → resourcesPath/app.db
  // Dev: the file produced by `npm run build:seeddb`.
  return isDev
    ? path.join(process.cwd(), "resources", "app.db")
    : path.join(process.resourcesPath, "app.db");
}

function userDbPath(): string {
  return path.join(app.getPath("userData"), "meraglym.db");
}

/** Copy the bundled seed database into the writable user directory on first run. */
function ensureUserDatabase(): string {
  const target = userDbPath();
  if (!fs.existsSync(target)) {
    const seed = seedDbPath();
    if (fs.existsSync(seed)) {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(seed, target);
    }
    // If no seed ships, better-sqlite3 will create an empty file; the app's
    // "refresh sources" action can then populate it from the bundled arf.json.
  }
  return target;
}

function findFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.on("error", reject);
    srv.listen(0, "127.0.0.1", () => {
      const address = srv.address();
      if (address && typeof address === "object") {
        const { port } = address;
        srv.close(() => resolve(port));
      } else {
        srv.close(() => reject(new Error("Could not determine a free port")));
      }
    });
  });
}

function waitForServer(port: number, timeoutMs = 30000): Promise<void> {
  const start = Date.now();
  const url = `http://127.0.0.1:${port}/`;
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(url, (res) => {
        res.resume();
        resolve();
      });
      req.on("error", () => {
        if (Date.now() - start > timeoutMs) {
          reject(new Error("Timed out waiting for the local server to start"));
        } else {
          setTimeout(attempt, 300);
        }
      });
    };
    attempt();
  });
}

let serverProcess: UtilityProcess | null = null;
let mainWindow: BrowserWindow | null = null;

async function startServer(): Promise<number> {
  const port = await findFreePort();
  const serverJs = standaloneServerPath();
  const dbPath = ensureUserDatabase();

  serverProcess = utilityProcess.fork(serverJs, [], {
    cwd: path.dirname(serverJs),
    stdio: "pipe",
    env: {
      ...process.env,
      NODE_ENV: "production",
      PORT: String(port),
      HOSTNAME: "127.0.0.1",
      MERAGLYM_DB_MODE: "local",
      MERAGLYM_SQLITE_PATH: dbPath,
    },
  });

  serverProcess.stdout?.on("data", (d) => process.stdout.write(`[next] ${d}`));
  serverProcess.stderr?.on("data", (d) => process.stderr.write(`[next] ${d}`));

  await waitForServer(port);
  return port;
}

function createWindow(baseUrl: string): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: "#0a0e14",
    title: "MERAGLYM",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const origin = new URL(baseUrl).origin;
  mainWindow.once("ready-to-show", () => mainWindow?.show());
  mainWindow.loadURL(baseUrl);

  // Open external links (target=_blank / http links) in the system browser.
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith(origin)) return { action: "allow" };
    shell.openExternal(url);
    return { action: "deny" };
  });
  mainWindow.webContents.on("will-navigate", (event, url) => {
    if (!url.startsWith(origin)) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function stopServer(): void {
  if (serverProcess) {
    serverProcess.kill();
    serverProcess = null;
  }
}

// Ensure only one instance runs (so the DB file is not opened twice).
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    try {
      // In `dev:desktop`, point the window at an already-running `next dev`
      // server instead of forking the production standalone build.
      const devUrl = process.env.MERAGLYM_DEV_URL;
      if (devUrl) {
        createWindow(devUrl);
      } else {
        const port = await startServer();
        createWindow(`http://127.0.0.1:${port}/`);
      }
    } catch (err) {
      console.error("Failed to start MERAGLYM:", err);
      app.quit();
    }

    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0 && serverProcess) {
        // Server already running; recreate the window against the same port is
        // non-trivial without tracking the port, so start fresh.
      }
    });
  });

  app.on("window-all-closed", () => {
    stopServer();
    if (process.platform !== "darwin") app.quit();
  });

  app.on("before-quit", stopServer);
}
