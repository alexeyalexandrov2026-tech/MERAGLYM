"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import { dictionaries, Locale, i18nConfig } from "./i18n";

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider = ({ children }: { children: ReactNode }) => {
  const [locale, setLocale] = useState<Locale>(i18nConfig.defaultLocale);

  const t = (key: string): string => {
    const keys = key.split(".");
    let value: any = dictionaries[locale];
    for (const k of keys) {
      if (value === undefined) break;
      value = value[k];
    }
    
    if (value === undefined) {
      let fallbackValue: any = dictionaries["en"];
      for (const k of keys) {
        if (fallbackValue === undefined) return key;
        fallbackValue = fallbackValue[k];
      }
      return fallbackValue as string;
    }
    return value as string;
  };

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error("useI18n must be used within an I18nProvider");
  }
  return context;
};
