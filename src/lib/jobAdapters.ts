/**
 * Catalogue of OSINT adapters that the Python worker (python/meraglym/osint)
 * can run. Shared by the /api/jobs route (validation) and the Jobs panel (UI).
 * Keep identifiers in sync with ALL_ADAPTER_IDENTIFIERS in
 * python/meraglym/osint/__init__.py.
 */

export type AdapterInput =
  | "inn"
  | "email"
  | "username"
  | "name"
  | "bssid"
  | "url"
  | "wallet"
  | "ip"
  | "onion"
  | "domain"
  | "indicator"
  | "stix";

export interface JobAdapter {
  id: string;
  label: string;
  region: "RU" | "GLOBAL";
  input: AdapterInput;
  placeholder: string;
  /** Short note on what the worker host needs (shown in the UI). */
  requires?: string;
}

export const JOB_ADAPTERS: readonly JobAdapter[] = [
  { id: "egrul_registry", label: "ЕГРЮЛ/ЕГРИП (egrul.nalog.ru)", region: "RU", input: "inn", placeholder: "7707083893", requires: "RU IP / RU_PROXY_URL" },
  { id: "fns_tax", label: "ФНС «Прозрачный бизнес»", region: "RU", input: "inn", placeholder: "7707083893", requires: "RU IP / RU_PROXY_URL" },
  { id: "rfsd_financials", label: "ГИР БО — бухотчётность (bo.nalog.ru)", region: "RU", input: "inn", placeholder: "7707083893", requires: "RU IP / RU_PROXY_URL" },
  { id: "efrsb_bankruptcy", label: "ЕФРСБ — банкротства", region: "RU", input: "inn", placeholder: "7707083893", requires: "RU IP / RU_PROXY_URL" },
  { id: "fssp_check", label: "ФССП — исполнительные производства", region: "RU", input: "inn", placeholder: "7707083893", requires: "RU IP / RU_PROXY_URL" },
  { id: "kad_arbitr", label: "КАД — арбитражные дела", region: "RU", input: "inn", placeholder: "7707083893", requires: "RU IP / RU_PROXY_URL" },
  { id: "sudrf_courts", label: "ГАС «Правосудие» (sudrf)", region: "RU", input: "name", placeholder: "ПАО Сбербанк", requires: "RU IP / RU_PROXY_URL" },
  { id: "mvd_wanted", label: "МВД — федеральный розыск", region: "RU", input: "name", placeholder: "Иванов Иван", requires: "RU IP / RU_PROXY_URL" },
  { id: "holehe_recon", label: "Holehe — email на сайтах", region: "GLOBAL", input: "email", placeholder: "user@example.com" },
  { id: "email_recon", label: "GHunt — Google-аккаунт по email", region: "GLOBAL", input: "email", placeholder: "user@gmail.com", requires: "GHunt session" },
  { id: "social_recon", label: "Maigret + Social Analyzer — username", region: "GLOBAL", input: "username", placeholder: "johndoe" },
  { id: "geospatial_mapper", label: "GeoWiFi — геолокация BSSID/SSID", region: "GLOBAL", input: "bssid", placeholder: "00:0C:42:1F:65:E9" },
  { id: "metadata_extractor", label: "EXIF / метаданные файла по URL", region: "GLOBAL", input: "url", placeholder: "https://example.com/photo.jpg" },
  { id: "crypto_recon", label: "Крипто-кошелёк (BTC / ETH)", region: "GLOBAL", input: "wallet", placeholder: "bc1q… / 0x…", requires: "ETH: ETHERSCAN_API_KEY" },
  { id: "camera_recon", label: "IP-камеры (HTTP/RTSP/ONVIF)", region: "GLOBAL", input: "ip", placeholder: "192.168.1.10", requires: "public IPs disabled by default" },
  { id: "darkweb_mapper", label: "TorBot — .onion crawler", region: "GLOBAL", input: "onion", placeholder: "http://…56 chars….onion" },
  { id: "spiderfoot_meta", label: "SpiderFoot — домен/IP", region: "GLOBAL", input: "domain", placeholder: "example.com" },
  { id: "opencti_connector", label: "OpenCTI — поиск индикатора", region: "GLOBAL", input: "indicator", placeholder: "8.8.8.8", requires: "OPENCTI_URL + OPENCTI_TOKEN" },
  { id: "stix_ingest", label: "STIX 2.1 — импорт объектов", region: "GLOBAL", input: "stix", placeholder: '[{"type":"threat-actor","id":"threat-actor--1","name":"APT28"}]' },
] as const;

const VALIDATORS: Record<Exclude<AdapterInput, "stix">, RegExp> = {
  inn: /^(\d{10}|\d{12})$/,
  email: /^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$/,
  username: /^@?[A-Za-z0-9_.-]{2,64}$/,
  name: /^[\p{L}\p{N} .,'"«»()-]{2,200}$/u,
  bssid: /^(([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}|[\w .-]{1,32})$/,
  url: /^https?:\/\/[^\s]{3,2000}$/,
  wallet: /^(bc1[a-z0-9]{25,87}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|0x[0-9a-fA-F]{40})$/,
  ip: /^[0-9a-fA-F:.]{2,45}(\/\d{1,3})?$/,
  onion: /^(https?:\/\/)?[a-z2-7]{56}\.onion(\/[^\s]*)?$/,
  domain: /^[A-Za-z0-9@._:-]{1,253}$/,
  indicator: /^[^\s]{1,500}$/,
};

export function findAdapter(id: unknown): JobAdapter | undefined {
  return typeof id === "string" ? JOB_ADAPTERS.find((a) => a.id === id) : undefined;
}

export type BuiltPayload =
  | { ok: true; payload: Record<string, unknown> }
  | { ok: false; error: string };

/** Validate the user's target for an adapter and build the worker payload. */
export function buildJobPayload(adapterId: unknown, target: unknown): BuiltPayload {
  const adapter = findAdapter(adapterId);
  if (!adapter) return { ok: false, error: "Unknown adapter" };
  if (typeof target !== "string" || target.trim().length === 0 || target.length > 20000) {
    return { ok: false, error: "Target is required" };
  }
  const value = target.trim();
  if (adapter.input === "stix") {
    try {
      const parsed: unknown = JSON.parse(value);
      const objects = Array.isArray(parsed)
        ? parsed
        : (parsed as { objects?: unknown })?.objects;
      if (!Array.isArray(objects) || objects.length === 0 || objects.length > 1000) {
        return { ok: false, error: "STIX input must be a JSON array (or bundle) with 1-1000 objects" };
      }
      return { ok: true, payload: { adapter_identifier: adapter.id, objects } };
    } catch {
      return { ok: false, error: "STIX input must be valid JSON" };
    }
  }
  if (!VALIDATORS[adapter.input].test(value)) {
    return { ok: false, error: `Invalid ${adapter.input} for ${adapter.id}` };
  }
  return { ok: true, payload: { adapter_identifier: adapter.id, value } };
}
