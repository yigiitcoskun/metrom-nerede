import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  RefreshControl,
  Switch,
  TouchableOpacity,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation';
import {
  getStationsWithArrivals,
  getVerilerStations,
  getTramStations,
  type StationWithArrivals,
  type VerilerStation,
} from '../api';

type Props = NativeStackScreenProps<RootStackParamList, 'Stations'>;

type StationRow = VerilerStation | StationWithArrivals;

export function StationsScreen({ route, navigation }: Props) {
  const { routeId, routeShortName, routeLongName, lineCode, lineName } = route.params;
  const isVerilerFlow = Boolean(lineCode);
  const [stations, setStations] = useState<StationRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useLive, setUseLive] = useState(isVerilerFlow);

  const load = (isRefresh = false, useLiveParam?: boolean) => {
    const live = useLiveParam ?? useLive;
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    if (isVerilerFlow && lineCode) {
      const fetchStations = lineCode.toUpperCase().startsWith('T')
        ? getTramStations(lineCode)
        : getVerilerStations(lineCode);
      fetchStations
        .then(setStations)
        .catch((e) => setError(e.message ?? 'Yüklenemedi'))
        .finally(() => {
          setLoading(false);
          setRefreshing(false);
        });
    } else if (routeId) {
      getStationsWithArrivals(routeId, live)
        .then(setStations)
        .catch((e) => setError(e.message ?? 'Yüklenemedi'))
        .finally(() => {
          setLoading(false);
          setRefreshing(false);
        });
    } else {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, [routeId, lineCode]);

  const onLiveToggle = (value: boolean) => {
    setUseLive(value);
    if (!isVerilerFlow && routeId) {
      setLoading(true);
      setError(null);
      getStationsWithArrivals(routeId, value)
        .then(setStations)
        .catch((e) => setError(e.message ?? 'Yüklenemedi'))
        .finally(() => setLoading(false));
    }
  };

  const onStationPress = (item: StationRow) => {
    if (!isVerilerFlow || !lineCode) return;
    const s = item as VerilerStation;
    navigation.navigate('StationDepartures', {
      lineCode,
      lineName: lineName ?? '',
      stationId: String(s.stationId),
      stationName: s.name,
    });
  };

  if (loading && stations.length === 0) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Duraklar yükleniyor...</Text>
      </View>
    );
  }

  const title = isVerilerFlow ? lineCode ?? '' : routeShortName ?? '';
  const subtitle = isVerilerFlow ? lineName ?? '' : routeLongName ?? '';

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.lineBadge}>{title}</Text>
            <Text style={styles.lineLong} numberOfLines={2}>
              {subtitle}
            </Text>
          </View>
          {!isVerilerFlow && (
            <View style={styles.liveRow}>
              <Text style={styles.liveLabel}>Canlı</Text>
              <Switch
                value={useLive}
                onValueChange={onLiveToggle}
                trackColor={{ false: '#334155', true: '#0ea5e9' }}
                thumbColor="#f8fafc"
              />
            </View>
          )}
        </View>
      </View>
      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}
      <FlatList
        data={stations}
        keyExtractor={(item) =>
          (item as VerilerStation).stationId != null
            ? String((item as VerilerStation).stationId)
            : (item as StationWithArrivals).stop_id
        }
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => load(true, useLive)}
            tintColor="#38bdf8"
          />
        }
        renderItem={({ item }) => {
          const stopName =
            (item as VerilerStation).name ?? (item as StationWithArrivals).stop_name;
          if (isVerilerFlow) {
            return (
              <TouchableOpacity
                style={styles.stationCard}
                onPress={() => onStationPress(item)}
                activeOpacity={0.7}>
                <Text style={styles.stationName}>{stopName}</Text>
                <Text style={styles.tapHint}>Seferler için dokun</Text>
              </TouchableOpacity>
            );
          }
          const withArrivals = item as StationWithArrivals;
          return (
            <View style={styles.stationCard}>
              <Text style={styles.stationName}>{stopName}</Text>
              <View style={styles.arrivals}>
                {withArrivals.arrivals?.length === 0 ? (
                  <Text style={styles.direction}>—</Text>
                ) : (
                  withArrivals.arrivals?.map((a, i) => (
                    <View key={i} style={styles.arrivalRow}>
                      <Text style={styles.direction} numberOfLines={1}>
                        {a.direction} yönü
                      </Text>
                      <Text style={styles.minutes}>
                        {a.display ?? (a.minutes != null ? `${a.minutes} dk` : '—')}
                      </Text>
                    </View>
                  ))
                )}
              </View>
            </View>
          );
        }}
      />
    </View>
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
  header: {
    padding: 20,
    paddingTop: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  liveRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  liveLabel: {
    fontSize: 13,
    color: '#94a3b8',
  },
  lineBadge: {
    fontSize: 24,
    fontWeight: '700',
    color: '#38bdf8',
  },
  lineLong: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  list: {
    padding: 16,
    paddingBottom: 32,
  },
  stationCard: {
    backgroundColor: '#1e293b',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  stationName: {
    fontSize: 17,
    fontWeight: '600',
    color: '#f8fafc',
  },
  tapHint: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 4,
  },
  arrivals: {
    gap: 6,
  },
  arrivalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  direction: {
    fontSize: 14,
    color: '#94a3b8',
    flex: 1,
  },
  minutes: {
    fontSize: 15,
    fontWeight: '600',
    color: '#38bdf8',
    marginLeft: 8,
  },
  loadingText: {
    color: '#94a3b8',
    marginTop: 12,
  },
  errorBanner: {
    backgroundColor: 'rgba(248,113,113,0.2)',
    padding: 12,
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 8,
  },
  errorText: {
    color: '#f87171',
    fontSize: 14,
  },
});
