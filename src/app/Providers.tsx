"use client";

import { ReactNode } from "react";
import { I18nProvider } from "@/lib/i18nContext";

export function Providers({ children }: { children: ReactNode }) {
  return <I18nProvider>{children}</I18nProvider>;
}
