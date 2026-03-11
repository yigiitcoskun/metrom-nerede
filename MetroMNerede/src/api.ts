/**
 * Backend API base URL.
 * - iOS Simulator: 127.0.0.1
 * - Android Emulator: 10.0.2.2
 * - Gerçek cihaz (iPhone/Android): Bilgisayarının yerel IP'si.
 *   Aynı Wi-Fi'de olmalı. Örnek: 192.168.1.42
 */
import { Platform } from 'react-native';

// iOS için backend adresi:
// - Simulator kullanıyorsan: '127.0.0.1'
// - Gerçek iPhone kullanıyorsan: bilgisayarının IP'si (örn. '192.168.0.105')
//   IP öğrenmek: Terminal'de  ifconfig | grep "inet " | grep -v 127
const DEV_BACKEND_IP = '192.168.1.106';

function getDevApiBase(): string {
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:5000'; // Android emulator
  }
  return `http://${DEV_BACKEND_IP}:5000`;
}

// Production: Vercel deploy sonrası buraya kendi URL'ini yaz (örn. https://metrom-nerede-api.vercel.app)
export const API_BASE = __DEV__ ? getDevApiBase() : 'https://your-backend.vercel.app';

export type CategoryKey = 'metrolar' | 'tramvaylar';

export interface RouteLine {
  route_id: string;
  route_short_name: string;
  route_long_name: string;
}

/** metro-lines.json metro array'inden hat: code (M1A, M2...) + name */
export interface VerilerLine {
  code: string;
  name: string;
  lineId?: number;
}

/** metro-lines.json'dan durak */
export interface VerilerStation {
  stationId: number;
  name: string;
}

/** veriler stations-with-arrivals: durak + iki route (direction = route.name, minutes) */
export interface VerilerStationWithArrivals {
  stationId: number;
  name: string;
  stop_id: string;
  stop_name: string;
  arrivals: { direction: string; minutes: number | null; display?: string | null }[];
}

export interface Station {
  stop_id: string;
  stop_name: string;
}

export interface ArrivalItem {
  direction: string;
  minutes: number | null;
  display?: string | null; // e.g. ">2 saat" when minutes > 120
}

export interface StationWithArrivals {
  stop_id: string;
  stop_name: string;
  arrivals: ArrivalItem[];
}

export async function getCategories(): Promise<{
  metrolar: RouteLine[];
  tramvaylar: RouteLine[];
}> {
  const r = await fetch(`${API_BASE}/api/categories`);
  if (!r.ok) throw new Error('API categories failed');
  return r.json();
}

export async function getLines(category: CategoryKey): Promise<RouteLine[]> {
  const r = await fetch(`${API_BASE}/api/lines/${category}`);
  if (!r.ok) throw new Error('API lines failed');
  return r.json();
}

/** Metrolar için: metro-lines.json metro array → M1A, M1B, M2... (code + name) */
export async function getVerilerLines(): Promise<VerilerLine[]> {
  const r = await fetch(`${API_BASE}/api/veriler/lines`);
  if (!r.ok) throw new Error('API veriler lines failed');
  return r.json();
}

/** Seçilen metro hattının durakları (Atatürk Havalimanı, DTM-İstanbul Fuar Merkezi, ...) */
export async function getVerilerStations(lineCode: string): Promise<VerilerStation[]> {
  const r = await fetch(`${API_BASE}/api/veriler/lines/${encodeURIComponent(lineCode)}/stations`);
  if (!r.ok) throw new Error('API veriler stations failed');
  return r.json();
}

/** Duraklar + her biri için route'lar (route.name → X dk) */
export async function getVerilerStationsWithArrivals(
  lineCode: string,
): Promise<VerilerStationWithArrivals[]> {
  const r = await fetch(
    `${API_BASE}/api/veriler/lines/${encodeURIComponent(lineCode)}/stations-with-arrivals`,
  );
  if (!r.ok) throw new Error('API veriler stations-with-arrivals failed');
  return r.json();
}

/** Tramvaylar için: tram-lines.json tram array → T1, T3, T4, T5... (code + name) */
export async function getTramLines(): Promise<VerilerLine[]> {
  const r = await fetch(`${API_BASE}/api/tram/lines`);
  if (!r.ok) throw new Error('API tram lines failed');
  return r.json();
}

/** Seçilen tramvay hattının durakları */
export async function getTramStations(lineCode: string): Promise<VerilerStation[]> {
  const r = await fetch(`${API_BASE}/api/tram/lines/${encodeURIComponent(lineCode)}/stations`);
  if (!r.ok) throw new Error('API tram stations failed');
  return r.json();
}

/** Tramvay durakları + her biri için route'lar (route.name → X dk) */
export async function getTramStationsWithArrivals(
  lineCode: string,
): Promise<VerilerStationWithArrivals[]> {
  const r = await fetch(
    `${API_BASE}/api/tram/lines/${encodeURIComponent(lineCode)}/stations-with-arrivals`,
  );
  if (!r.ok) throw new Error('API tram stations-with-arrivals failed');
  return r.json();
}

export async function getStations(routeId: string): Promise<Station[]> {
  const r = await fetch(`${API_BASE}/api/route/${routeId}/stations`);
  if (!r.ok) throw new Error('API stations failed');
  return r.json();
}

export async function getStationsWithArrivals(
  routeId: string,
  useLive?: boolean,
): Promise<StationWithArrivals[]> {
  const url = useLive
    ? `${API_BASE}/api/route/${routeId}/stations-with-arrivals?live=1`
    : `${API_BASE}/api/route/${routeId}/stations-with-arrivals`;
  const r = await fetch(url);
  if (!r.ok) throw new Error('API stations-with-arrivals failed');
  return r.json();
}

/** Metro İstanbul canlı sefer (sadece desteklenen hatlar, örn. M7). Rate limit: 30/dk. */
export interface LiveDepartureYon {
  yon: string;
  minutes: number | null;
  seferler: { yon: string; zaman: string; minutes: number | null }[];
}

export async function getLiveDepartures(
  hat: string,
  istasyon: string,
): Promise<{
  kaynak: string;
  istasyon: string;
  hat: string;
  yonler: LiveDepartureYon[];
  hata?: string;
}> {
  const params = new URLSearchParams({ hat, istasyon });
  const r = await fetch(`${API_BASE}/api/live/departures?${params}`);
  if (r.status === 429)
    throw new Error('Çok fazla istek. Lütfen 1 dakika bekleyin.');
  if (!r.ok) throw new Error('Canlı veri alınamadı');
  return r.json();
}
