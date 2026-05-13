type AppNameListener = (name: string) => void;
type CompanyNameListener = (name: string) => void;

let appName = "UNIK ERP";
let companyName = "";
const appNameListeners = new Set<AppNameListener>();
const companyNameListeners = new Set<CompanyNameListener>();

const APP_NAME_KEY = "unik-app-name";
const COMPANY_NAME_KEY = "unik-company-name";

try {
  const stored = localStorage.getItem(APP_NAME_KEY);
  if (stored) appName = stored;
} catch {}
try {
  const stored = localStorage.getItem(COMPANY_NAME_KEY);
  if (stored) companyName = stored;
} catch {}

// --- App name ---
export function getAppName(): string { return appName; }

export function setAppName(name: string): void {
  if (!name || name === appName) return;
  appName = name;
  try { localStorage.setItem(APP_NAME_KEY, name); } catch {}
  for (const fn of appNameListeners) fn(name);
}

export function subscribeAppName(fn: AppNameListener): () => void {
  appNameListeners.add(fn);
  fn(appName);
  return () => { appNameListeners.delete(fn); };
}

// --- Company name ---
export function getCompanyName(): string { return companyName; }

export function setCompanyName(name: string): void {
  if (name === companyName) return;
  companyName = name;
  try { localStorage.setItem(COMPANY_NAME_KEY, name); } catch {}
  for (const fn of companyNameListeners) fn(name);
}

export function subscribeCompanyName(fn: CompanyNameListener): () => void {
  companyNameListeners.add(fn);
  fn(companyName);
  return () => { companyNameListeners.delete(fn); };
}
