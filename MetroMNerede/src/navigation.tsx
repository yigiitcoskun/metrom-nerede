import type { RouteProp } from '@react-navigation/native';

export type RootStackParamList = {
  Home: undefined;
  Lines: { category: 'metrolar' | 'tramvaylar' };
  Stations: {
    routeId?: string;
    routeShortName?: string;
    routeLongName?: string;
    /** Metrolar/Tramvay (veriler): hat kodu ve adı */
    lineCode?: string;
    lineName?: string;
  };
  /** Durağa tıklanınca: canlı sefer listesi (4 sefer/yön) */
  StationDepartures: {
    lineCode: string;
    lineName?: string;
    stationId: string;
    stationName: string;
  };
};

export type LinesRouteProp = RouteProp<RootStackParamList, 'Lines'>;
export type StationsRouteProp = RouteProp<RootStackParamList, 'Stations'>;
