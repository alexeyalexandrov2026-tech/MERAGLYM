export const i18nConfig = {
  defaultLocale: 'en',
  locales: ['en', 'ru'],
} as const;

export type Locale = (typeof i18nConfig)['locales'][number];

// Placeholder for translation dictionaries. 
// A full implementation would likely use next-intl or similar to load JSON dictionaries.
const dictionaries = {
  en: {
    nav: {
      overview: "Overview",
      hierarchy: "Hierarchy",
      search: "Search",
      jobs: "Jobs",
      intelligence: "Intelligence",
    }
  },
  ru: {
    nav: {
      overview: "Обзор",
      hierarchy: "Иерархия",
      search: "Поиск",
      jobs: "Задачи",
      intelligence: "Разведка",
    }
  }
};

export const getDictionary = (locale: Locale) => dictionaries[locale] || dictionaries[i18nConfig.defaultLocale];
