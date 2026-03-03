import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

export function HomeScreen({ navigation }: Props) {
  const openCategory = (category: 'metrolar' | 'tramvaylar') => {
    navigation.navigate('Lines', { category });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Metrom Nerede?</Text>
      <Text style={styles.subtitle}>Hat seçin</Text>

      <TouchableOpacity
        style={[styles.card, styles.metro]}
        onPress={() => openCategory('metrolar')}>
        <Text style={styles.cardTitle}>Metrolar</Text>
        <Text style={styles.cardSubtitle}>M1A, M2, M3, M4, M5, M6, M7, M8, M9</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.card, styles.tram]}
        onPress={() => openCategory('tramvaylar')}>
        <Text style={styles.cardTitle}>Tramvaylar</Text>
        <Text style={styles.cardSubtitle}>T1, T3, T4, T5</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
    padding: 24,
    paddingTop: 48,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#94a3b8',
    marginBottom: 32,
  },
  card: {
    padding: 20,
    borderRadius: 16,
    marginBottom: 16,
  },
  metro: {
    backgroundColor: '#1e40af',
  },
  tram: {
    backgroundColor: '#15803d',
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
  },
  cardSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.85)',
    marginTop: 4,
  },
});
