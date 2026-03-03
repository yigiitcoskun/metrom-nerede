/**
 * Metrom Nerede? – İstanbul metro/tramvay sefer bilgisi
 * @format
 */

import React from 'react';
import { StatusBar } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import type { RootStackParamList } from './src/navigation';
import { HomeScreen } from './src/screens/HomeScreen';
import { LinesScreen } from './src/screens/LinesScreen';
import { StationsScreen } from './src/screens/StationsScreen';
import { StationDeparturesScreen } from './src/screens/StationDeparturesScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();

function App(): React.JSX.Element {
  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" backgroundColor="#0f172a" />
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Home"
          screenOptions={{
            headerStyle: { backgroundColor: '#0f172a' },
            headerTintColor: '#f8fafc',
            headerTitleStyle: { fontWeight: '600', fontSize: 18 },
            headerBackTitleVisible: false,
            contentStyle: { backgroundColor: '#0f172a' },
          }}>
          <Stack.Screen
            name="Home"
            component={HomeScreen}
            options={{ title: 'Metrom Nerede?' }}
          />
          <Stack.Screen
            name="Lines"
            component={LinesScreen}
            options={({ route }) => ({
              title:
              route.params.category === 'metrolar' ? 'Metrolar' : 'Tramvaylar',
            })}
          />
          <Stack.Screen
            name="Stations"
            component={StationsScreen}
            options={({ route }) => ({
              title: route.params.routeShortName ?? route.params.lineCode ?? 'Duraklar',
            })}
          />
          <Stack.Screen
            name="StationDepartures"
            component={StationDeparturesScreen}
            options={({ route }) => ({
              title: route.params.stationName,
            })}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

export default App;
