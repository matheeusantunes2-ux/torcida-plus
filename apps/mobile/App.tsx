import React, { useState } from 'react';
import {
  SafeAreaView, ScrollView, StatusBar,
  StyleSheet, Text, TouchableOpacity, View
} from 'react-native';

const RED = '#E52535';
const BG = '#090909';
const CARD = '#171717';

export default function App() {
  const [tab, setTab] = useState('Início');
  const [liked, setLiked] = useState(false);

  const tabs = ['Início', 'Torcidas', 'Eventos', 'Loja', 'Perfil'];

  return (
    <SafeAreaView style={s.safe}>
      <StatusBar barStyle="light-content" />

      <View style={s.header}>
        <View>
          <Text style={s.logo}>TORCIDA<Text style={{color: RED}}>+</Text></Text>
          <Text style={s.subtitle}>A PAIXÃO NOS UNE</Text>
        </View>
        <TouchableOpacity onPress={() => setTab('Perfil')} style={s.avatar}>
          <Text style={s.white}>T+</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={s.content}>
        {tab === 'Início' ? (
          <>
            <View style={s.hero}>
              <Text style={s.red}>SUA TORCIDA. SUA VOZ.</Text>
              <Text style={s.title}>Viva o futebol em outro nível.</Text>
              <Text style={s.text}>
                Conecte-se com sua torcida, acompanhe eventos e viva cada momento.
              </Text>
              <TouchableOpacity style={s.button} onPress={() => setTab('Torcidas')}>
                <Text style={s.white}>EXPLORAR TORCIDAS</Text>
              </TouchableOpacity>
            </View>

            <Text style={s.heading}>Comunidades</Text>
            <View style={s.row}>
              {['Flamengo', 'Botafogo', 'Vasco', 'Fluminense'].map((team) => (
                <TouchableOpacity key={team} style={s.team} onPress={() => setTab('Torcidas')}>
                  <Text style={s.white}>{team}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={s.heading}>Últimas publicações</Text>
            <View style={s.post}>
              <Text style={s.red}>NAÇÃO RUBRO-NEGRA</Text>
              <Text style={s.postTitle}>A paixão não se explica. Se vive!</Text>
              <Text style={s.text}>
                Dia de jogo é dia de mostrar a força da nossa torcida. Quem vai estar presente?
              </Text>
              <TouchableOpacity onPress={() => setLiked(!liked)}>
                <Text style={[s.action, liked && {color: RED}]}>
                  {liked ? '♥ Curtido' : '♡ Curtir'}  •  128 curtidas
                </Text>
              </TouchableOpacity>
            </View>

            <View style={s.post}>
              <Text style={s.red}>TORCIDA EM MOVIMENTO</Text>
              <Text style={s.postTitle}>Próxima caravana confirmada!</Text>
              <Text style={s.text}>
                Organize sua viagem e acompanhe os próximos eventos da torcida.
              </Text>
              <Text style={s.action}>24 comentários</Text>
            </View>
          </>
        ) : (
          <View style={s.other}>
            <Text style={s.title}>{tab}</Text>
            <Text style={s.text}>
              Esta área do TORCIDA+ será desenvolvida na próxima etapa.
            </Text>
            <TouchableOpacity style={s.button} onPress={() => setTab('Início')}>
              <Text style={s.white}>VOLTAR AO INÍCIO</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>

      <View style={s.nav}>
        {tabs.map((item, i) => (
          <TouchableOpacity key={item} style={s.navItem} onPress={() => setTab(item)}>
            <Text style={[s.navIcon, tab === item && {color: RED}]}>
              {['⌂', '⚑', '◷', '▣', '●'][i]}
            </Text>
            <Text style={[s.navText, tab === item && {color: RED}]}>{item}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: {flex: 1, backgroundColor: BG},
  header: {height: 72, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: '#292929'},
  logo: {color: '#FFF', fontSize: 24, fontWeight: '900'},
  subtitle: {color: '#AAA', fontSize: 9, letterSpacing: 2},
  avatar: {backgroundColor: RED, width: 42, height: 42, borderRadius: 14, alignItems: 'center', justifyContent: 'center'},
  white: {color: '#FFF', fontWeight: '800', textAlign: 'center'},
  content: {padding: 16, paddingBottom: 24},
  hero: {backgroundColor: CARD, padding: 20, borderRadius: 20, marginBottom: 24, borderWidth: 1, borderColor: '#303030'},
  red: {color: RED, fontSize: 11, fontWeight: '900', letterSpacing: 1},
  title: {color: '#FFF', fontSize: 28, fontWeight: '900', marginTop: 12},
  text: {color: '#CCC', fontSize: 14, lineHeight: 22, marginTop: 10},
  button: {backgroundColor: RED, padding: 15, borderRadius: 12, marginTop: 20},
  heading: {color: '#FFF', fontSize: 18, fontWeight: '900', marginBottom: 14, marginTop: 4},
  row: {flexDirection: 'row', flexWrap: 'wrap', marginBottom: 22},
  team: {backgroundColor: CARD, padding: 12, borderRadius: 12, marginRight: 8, marginBottom: 8},
  post: {backgroundColor: CARD, padding: 17, borderRadius: 16, marginBottom: 14, borderWidth: 1, borderColor: '#292929'},
  postTitle: {color: '#FFF', fontSize: 16, fontWeight: '800', marginTop: 10},
  action: {color: '#CCC', marginTop: 16, fontSize: 12},
  other: {paddingVertical: 80},
  nav: {height: 68, flexDirection: 'row', backgroundColor: '#111', borderTopWidth: 1, borderTopColor: '#292929'},
  navItem: {flex: 1, alignItems: 'center', justifyContent: 'center'},
  navIcon: {fontSize: 19, color: '#AAA'},
  navText: {fontSize: 10, color: '#AAA', marginTop: 4}
});
