import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation';
import {
  getLines,
  getVerilerLines,
  getTramLines,
  type RouteLine,
  type VerilerLine,
} from '../api';
import type { CategoryKey } from '../api';

type Props = NativeStackScreenProps<RootStackParamList, 'Lines'>;

const CATEGORY_TITLES: Record<CategoryKey, string> = {
  metrolar: 'Metrolar',
  tramvaylar: 'Tramvaylar',
};

type LineItem = { type: 'veriler'; line: VerilerLine } | { type: 'gtfs'; line: RouteLine };

export function LinesScreen({ route, navigation }: Props) {
  const { category } = route.params;
  const [items, setItems] = useState<LineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (category === 'metrolar') {
      getVerilerLines()
        .then((data) => {
          if (!cancelled) setItems(data.map((line) => ({ type: 'veriler' as const, line })));
        })
        .catch((e) => {
          if (!cancelled) setError(e.message ?? 'Yüklenemedi');
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    } else if (category === 'tramvaylar') {
      getTramLines()
        .then((data) => {
          if (!cancelled) setItems(data.map((line) => ({ type: 'veriler' as const, line })));
        })
        .catch((e) => {
          if (!cancelled) setError(e.message ?? 'Yüklenemedi');
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    } else {
      getLines(category)
        .then((data) => {
          if (!cancelled) setItems(data.map((line) => ({ type: 'gtfs' as const, line })));
        })
        .catch((e) => {
          if (!cancelled) setError(e.message ?? 'Yüklenemedi');
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }
    return () => {
      cancelled = true;
    };
  }, [category]);

  const openStations = (item: LineItem) => {
    if (item.type === 'veriler') {
      navigation.navigate('Stations', {
        lineCode: item.line.code,
        lineName: item.line.name ?? item.line.code,
      });
    } else {
      navigation.navigate('Stations', {
        routeId: item.line.route_id,
        routeShortName: item.line.route_short_name,
        routeLongName: item.line.route_long_name,
      });
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Hatlar yükleniyor...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error}</Text>
        <Text style={styles.hint}>Backend çalışıyor mu? (port 5000)</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={items}
        keyExtractor={(item) =>
          item.type === 'veriler' ? item.line.code : item.line.route_id
        }
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.lineCard}
            onPress={() => openStations(item)}>
            <Text style={styles.lineShort}>
              {item.type === 'veriler' ? item.line.code : item.line.route_short_name}
            </Text>
            <Text style={styles.lineLong} numberOfLines={1}>
              {item.type === 'veriler' ? item.line.name : item.line.route_long_name}
            </Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
    paddingVertical: 16,
  },
  centered: {
    flex: 1,
    backgroundColor: '#0f172a',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  title: {
    fontSize: 22,
    fontWeight: '600',
    color: '#f8fafc',
    marginBottom: 16,
  },
  list: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  lineCard: {
    backgroundColor: '#1e293b',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  lineShort: {
    fontSize: 20,
    fontWeight: '700',
    color: '#38bdf8',
  },
  lineLong: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  loadingText: {
    color: '#94a3b8',
    marginTop: 12,
  },
  errorText: {
    color: '#f87171',
    fontSize: 16,
    textAlign: 'center',
  },
  hint: {
    color: '#64748b',
    marginTop: 8,
    fontSize: 14,
  },
});
