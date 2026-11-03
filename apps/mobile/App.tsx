import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Button,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import * as SecureStore from 'expo-secure-store';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000';

async function saveToken(token: string) {
  await SecureStore.setItemAsync('torcida_plus_token', token);
}

async function loadToken() {
  return SecureStore.getItemAsync('torcida_plus_token');
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const token = await loadToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};

  if (!response.ok) {
    throw new Error(payload.detail || payload.message || 'Erro na API');
  }

  return payload;
}

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [torcidas, setTorcidas] = useState<any[]>([]);

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const savedToken = await loadToken();
        setToken(savedToken);
        if (savedToken) {
          const data = await apiFetch('/api/torcidas/');
          setTorcidas(data || []);
        }
      } catch (error) {
        setMessage(error instanceof Error ? error.message : 'Não foi possível carregar os dados');
      } finally {
        setLoading(false);
      }
    };

    bootstrap();
  }, [token]);

  async function handleAuth() {
    try {
      setLoading(true);
      const endpoint = mode === 'login' ? '/api/auth/login/' : '/api/auth/cadastro/';
      const body =
        mode === 'login'
          ? { username, password }
          : { username, email, password };

      const result = mode === 'login' ? await apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify(body),
      }) : await apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify(body),
      });

      if (mode === 'login') {
        await saveToken(result.access);
        setToken(result.access);
        setMessage('Login realizado com sucesso!');
      } else {
        setMode('login');
        setMessage('Cadastro realizado. Agora faça login.');
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Não foi possível autenticar');
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    await SecureStore.deleteItemAsync('torcida_plus_token');
    setToken(null);
    setTorcidas([]);
    setMessage('Sessão encerrada.');
  }

  async function fetchTorcidas() {
    try {
      const data = await apiFetch('/api/torcidas/');
      setTorcidas(data || []);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Erro ao carregar torcidas');
    }
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.safeCenter}>
        <StatusBar barStyle="light-content" />
        <ActivityIndicator size="large" color="#F02036" />
        <Text style={styles.loadingText}>Carregando TORCIDA+</Text>
      </SafeAreaView>
    );
  }

  if (!token) {
    return (
      <SafeAreaView style={styles.safe}>
        <StatusBar barStyle="light-content" />
        <ScrollView contentContainerStyle={styles.authContainer}>
          <Text style={styles.logo}>TORCIDA<Text style={{ color: '#F02036' }}>+</Text></Text>
          <Text style={styles.subtitle}>A paixão do futebol em um só lugar.</Text>

          <TextInput
            style={styles.input}
            placeholder="Username"
            value={username}
            onChangeText={setUsername}
            placeholderTextColor="#8a8a93"
          />

          {mode === 'register' && (
            <TextInput
              style={styles.input}
              placeholder="E-mail"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              placeholderTextColor="#8a8a93"
            />
          )}

          <TextInput
            style={styles.input}
            placeholder="Senha"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            placeholderTextColor="#8a8a93"
          />

          {message ? <Text style={styles.message}>{message}</Text> : null}

          <Button title={mode === 'login' ? 'Entrar' : 'Criar conta'} color="#F02036" onPress={handleAuth} />
          <View style={{ height: 12 }} />
          <Button
            title={mode === 'login' ? 'Quero me cadastrar' : 'Voltar ao login'}
            color="#2b2b31"
            onPress={() => {
              setMode(mode === 'login' ? 'register' : 'login');
              setMessage('');
            }}
          />
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" />
      <ScrollView contentContainerStyle={styles.homeContainer}>
        <View style={styles.headerRow}>
          <Text style={styles.logoSmall}>TORCIDA<Text style={{ color: '#F02036' }}>+</Text></Text>
          <Button title="Sair" color="#2b2b31" onPress={handleLogout} />
        </View>

        <Text style={styles.heroTitle}>Bem-vindo ao seu espaço da torcida</Text>
        <Text style={styles.heroSubtitle}>Aqui você pode acompanhar as comunidades e o backend funcionando.</Text>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Minhas torcidas</Text>
          <Button title="Atualizar" color="#F02036" onPress={fetchTorcidas} />
          {torcidas.length === 0 ? (
            <Text style={styles.empty}>Nenhuma torcida cadastrada ainda.</Text>
          ) : (
            torcidas.map((torcida) => (
              <View key={torcida.id} style={styles.listRow}>
                <Text style={styles.listTitle}>{torcida.nome}</Text>
                <Text style={styles.listMeta}>slug: {torcida.slug}</Text>
              </View>
            ))
          )}
        </View>

        {message ? <Text style={styles.message}>{message}</Text> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#080809',
  },
  safeCenter: {
    flex: 1,
    backgroundColor: '#080809',
    justifyContent: 'center',
    alignItems: 'center',
  },
  authContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  homeContainer: {
    flexGrow: 1,
    padding: 20,
  },
  logo: {
    color: '#FFF',
    fontSize: 42,
    fontWeight: '900',
    letterSpacing: -1,
  },
  logoSmall: {
    color: '#FFF',
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: -1,
  },
  subtitle: {
    color: '#A4A4AE',
    fontSize: 16,
    marginTop: 8,
    marginBottom: 24,
  },
  heroTitle: {
    color: '#FFF',
    fontSize: 28,
    fontWeight: '900',
    marginTop: 14,
  },
  heroSubtitle: {
    color: '#A4A4AE',
    fontSize: 14,
    marginTop: 8,
    marginBottom: 16,
  },
  input: {
    backgroundColor: '#17171B',
    borderColor: '#292930',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: '#FFF',
    marginBottom: 12,
    fontSize: 16,
  },
  message: {
    color: '#F6B7C0',
    fontSize: 12,
    marginBottom: 12,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  card: {
    backgroundColor: '#17171B',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#292930',
    marginTop: 16,
  },
  cardTitle: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 10,
  },
  listRow: {
    backgroundColor: '#0e0e12',
    borderRadius: 12,
    padding: 12,
    marginTop: 10,
  },
  listTitle: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '700',
  },
  listMeta: {
    color: '#A4A4AE',
    fontSize: 12,
    marginTop: 4,
  },
  empty: {
    color: '#A4A4AE',
    marginTop: 8,
  },
  loadingText: {
    color: '#FFF',
    marginTop: 12,
    fontSize: 16,
    fontWeight: '700',
  },
});

