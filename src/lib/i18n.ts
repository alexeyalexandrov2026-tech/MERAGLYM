export const i18nConfig = {
  defaultLocale: 'en',
  locales: ['en', 'ru'],
} as const;

export type Locale = (typeof i18nConfig)['locales'][number];

export const dictionaries = {
  en: {
    nav: {
      overview: "OVERVIEW",
      osint: "OSINT HIERARCHY",
      search: "GLOBAL SEARCH",
      jobs: "SYSTEM JOBS",
    },
    dashboard: {
      title: "MERAGLYM SYSTEM OVERVIEW",
      welcome: "Welcome to the Meraglym OSINT Intelligence Platform. Select a module from the left navigation array to begin."
    },
    sidebar: {
      sysIndex: "SYS.INDEX",
      rootCategories: "ROOT_CATEGORIES",
      entries: "ENTRIES",
      loading: "..."
    },
    nodeView: {
      awaitingSelection: "AWAITING_TARGET_SELECTION",
      initiateUplink: "INITIATE_UPLINK ↗",
      description: "DESCRIPTION",
      status: "STATUS",
      bestFor: "BEST FOR",
      pricing: "PRICING",
      input: "INPUT",
      output: "OUTPUT",
      opsec: "OPSEC",
      opsecNote: "OPSEC NOTE"
    },
    searchPanel: {
      title: "SYSTEM SEARCH // GLOBAL",
      placeholder: "QUERY OSINT DATABASE...",
      searching: "[SEARCHING...]",
      noResults: "[NO RESULTS FOUND]",
      matches: "MATCHES // RANKED BY RELEVANCE"
    },
    jobsPanel: {
      title: "SYSTEM WORKER JOBS //",
      recent: "RECENT",
      refresh: "REFRESH",
      loading: "[LOADING JOB SCHEDULER...]",
      noJobs: "[NO JOBS FOUND IN DATABASE]",
      created: "CREATED:",
      started: "STARTED:",
      completed: "COMPLETED:",
      id: "ID:"
    },
    common: {
      language: "Language"
    }
  },
  ru: {
    nav: {
      overview: "ОБЗОР",
      osint: "ОСИНТ ИЕРАРХИЯ",
      search: "ГЛОБАЛЬНЫЙ ПОИСК",
      jobs: "СИСТЕМНЫЕ ЗАДАЧИ",
    },
    dashboard: {
      title: "СИСТЕМНЫЙ ОБЗОР MERAGLYM",
      welcome: "Добро пожаловать в платформу разведки Meraglym OSINT. Выберите модуль из левого навигационного массива, чтобы начать."
    },
    sidebar: {
      sysIndex: "СИСТ.ИНДЕКС",
      rootCategories: "КОРНЕВЫЕ_КАТЕГОРИИ",
      entries: "ЗАПИСЕЙ",
      loading: "..."
    },
    nodeView: {
      awaitingSelection: "ОЖИДАНИЕ_ВЫБОРА_ЦЕЛИ",
      initiateUplink: "ИНИЦИАЛИЗАЦИЯ_СВЯЗИ ↗",
      description: "ОПИСАНИЕ",
      status: "СТАТУС",
      bestFor: "ЛУЧШЕЕ ДЛЯ",
      pricing: "ЦЕНА",
      input: "ВВОД",
      output: "ВЫВОД",
      opsec: "OPSEC",
      opsecNote: "ПРИМЕЧАНИЕ OPSEC"
    },
    searchPanel: {
      title: "СИСТЕМНЫЙ ПОИСК // ГЛОБАЛЬНЫЙ",
      placeholder: "ЗАПРОС К БАЗЕ ДАННЫХ OSINT...",
      searching: "[ПОИСК...]",
      noResults: "[РЕЗУЛЬТАТЫ НЕ НАЙДЕНЫ]",
      matches: "СОВПАДЕНИЙ // ОТСОРТИРОВАНО ПО РЕЛЕВАНТНОСТИ"
    },
    jobsPanel: {
      title: "СИСТЕМНЫЕ ЗАДАЧИ //",
      recent: "НЕДАВНИХ",
      refresh: "ОБНОВИТЬ",
      loading: "[ЗАГРУЗКА ПЛАНИРОВЩИКА ЗАДАЧ...]",
      noJobs: "[ЗАДАЧИ В БАЗЕ ДАННЫХ НЕ НАЙДЕНЫ]",
      created: "СОЗДАНА:",
      started: "НАЧАТА:",
      completed: "ЗАВЕРШЕНА:",
      id: "ID:"
    },
    common: {
      language: "Язык"
    }
  }
};

