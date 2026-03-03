import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation';
import { getLiveDepartures, type LiveDepartureYon } from '../api';

const SEFER_LIMIT = 4;

type Props = NativeStackScreenProps<RootStackParamList, 'StationDepartures'>;

export function StationDeparturesScreen({ route }: Props) {
  const { lineCode, stationName } = route.params;
  const [data, setData] = useState<LiveDepartureYon[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    getLiveDepartures(lineCode, stationName)
      .then((res) => setData(res.yonler || []))
      .catch((e) => setError(e.message ?? 'Canlı veri alınamadı'))
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  };

  useEffect(() => {
    load();
  }, [lineCode, stationName]);

  if (loading && !data) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#38bdf8" />
        <Text style={styles.loadingText}>Seferler yükleniyor...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => load(true)}
          tintColor="#38bdf8"
        />
      }>
      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}
      {data &&
        (data.length === 0 ||
          data.filter((yon) => (yon.seferler?.length ?? 0) > 0).length === 0) &&
        !error && (
          <Text style={styles.empty}>Bu durak için sefer bilgisi yok.</Text>
        )}
      {data
        ?.filter((yon) => (yon.seferler?.length ?? 0) > 0)
        .map((yon: LiveDepartureYon, idx: number) => (
          <View key={idx} style={styles.yonBlock}>
            <Text style={styles.yonTitle}>{yon.yon}</Text>
            {(yon.seferler || [])
              .slice(0, SEFER_LIMIT)
              .map((s, i) => (
                <View key={i} style={styles.seferRow}>
                  <Text style={styles.zaman}>{s.zaman}</Text>
                  <Text style={styles.minutes}>
                    {s.minutes != null ? `${s.minutes} dk` : '—'}
                  </Text>
                </View>
              ))}
          </View>
        ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  centered: {
    flex: 1,
    backgroundColor: '#0f172a',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  loadingText: {
    color: '#94a3b8',
    marginTop: 12,
  },
  errorBanner: {
    backgroundColor: 'rgba(248,113,113,0.2)',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#f87171',
    fontSize: 14,
  },
  empty: {
    color: '#94a3b8',
    fontSize: 15,
  },
  yonBlock: {
    backgroundColor: '#1e293b',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  yonTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#38bdf8',
    marginBottom: 12,
  },
  seferRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  zaman: {
    fontSize: 16,
    color: '#f8fafc',
  },
  minutes: {
    fontSize: 15,
    fontWeight: '600',
    color: '#38bdf8',
  },
});
