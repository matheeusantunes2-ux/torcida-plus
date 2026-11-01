import React, { useState } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

const RED = '#F02036';
const BG = '#080809';
const CARD = '#17171B';
const MUTED = '#A4A4AE';
const BORDER = '#292930';

const tabs = [
  { name: 'Início', icon: '⌂' },
  { name: 'Chat', icon: '☏' },
  { name: 'Eventos', icon: '▦' },
  { name: 'Loja', icon: '▣' },
  { name: 'Perfil', icon: '●' },
];

const communities = [
  { name: 'Flamengo', emoji: '🔴', members: '25,4 mil' },
  { name: 'Vasco', emoji: '⚫', members: '18,2 mil' },
  { name: 'Botafogo', emoji: '⭐', members: '12,8 mil' },
  { name: 'Fluminense', emoji: '🟢', members: '10,1 mil' },
];

export default function App() {
  const [tab, setTab] = useState('Início');
  const [liked, setLiked] = useState<string[]>([]);
  const [joined, setJoined] = useState<string[]>([]);

  function toggleLike(id: string) {
    setLiked((old) =>
      old.includes(id) ? old.filter((item) => item !== id) : [...old, id]
    );
  }

  function toggleJoin(name: string) {
    setJoined((old) =>
      old.includes(name)
        ? old.filter((item) => item !== name)
        : [...old, name]
    );
  }

  function Header() {
    return (
      <View style={s.header}>
        <View>
          <Text style={s.logo}>
            TORCIDA<Text style={{ color: RED }}>+</Text>
          </Text>
          <Text style={s.tagline}>A PAIXÃO NOS UNE</Text>
        </View>
        <View style={s.headerActions}>
          <TouchableOpacity
            style={s.notification}
            onPress={() => setTab('Chat')}
          >
            <Text style={s.notificationIcon}>♧</Text>
            <View style={s.notificationDot} />
          </TouchableOpacity>
          <TouchableOpacity
            style={s.avatar}
            onPress={() => setTab('Perfil')}
          >
            <Text style={s.avatarText}>T+</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  function SectionTitle({
    title,
    action,
    onPress,
  }: {
    title: string;
    action?: string;
    onPress?: () => void;
  }) {
    return (
      <View style={s.sectionHeader}>
        <Text style={s.sectionTitle}>{title}</Text>
        {action ? (
          <TouchableOpacity onPress={onPress}>
            <Text style={s.seeAll}>{action} ›</Text>
          </TouchableOpacity>
        ) : null}
      </View>
    );
  }

  function Home() {
    return (
      <>
        <View style={s.welcome}>
          <View style={s.liveBadge}>
            <View style={s.liveDot} />
            <Text style={s.liveText}>A SUA COMUNIDADE</Text>
          </View>
          <Text style={s.heroTitle}>
            A paixão pelo futebol{'\n'}
            <Text style={{ color: RED }}>começa aqui.</Text>
          </Text>
          <Text style={s.heroDescription}>
            Encontre sua torcida, participe dos encontros e viva cada jogo
            junto de quem sente a mesma paixão.
          </Text>
          <TouchableOpacity
            style={s.primaryButton}
            onPress={() => setTab('Torcidas')}
          >
            <Text style={s.primaryButtonText}>EXPLORAR COMUNIDADES  →</Text>
          </TouchableOpacity>
          <View style={s.heroFooter}>
            <View style={s.avatarStack}>
              <Text style={s.stackEmoji}>⚽</Text>
              <Text style={s.stackEmoji}>🔥</Text>
              <Text style={s.stackEmoji}>🏟️</Text>
            </View>
            <Text style={s.heroFooterText}>A torcida é muito maior quando é junto.</Text>
          </View>
        </View>

        <SectionTitle
          title="Sua torcida"
          action="Ver todas"
          onPress={() => setTab('Torcidas')}
        />
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={s.communityScroll}
        >
          {communities.map((team) => (
            <TouchableOpacity
              key={team.name}
              style={s.communityCard}
              onPress={() => setTab('Torcidas')}
            >
              <View style={s.teamBadge}>
                <Text style={s.teamEmoji}>{team.emoji}</Text>
              </View>
              <Text style={s.teamName}>{team.name}</Text>
              <Text style={s.memberCount}>{team.members} membros</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <SectionTitle
          title="Acontece na torcida"
          action="Ver eventos"
          onPress={() => setTab('Eventos')}
        />
        <TouchableOpacity
          style={s.eventCard}
          onPress={() => setTab('Eventos')}
        >
          <View style={s.eventDate}>
            <Text style={s.eventDay}>08</Text>
            <Text style={s.eventMonth}>NOV</Text>
          </View>
          <View style={s.eventInfo}>
            <Text style={s.eventCategory}>ENCONTRO DA TORCIDA</Text>
            <Text style={s.eventTitle}>Pré-jogo e encontro da nação</Text>
            <Text style={s.eventDetail}>◷ 16:00  •  Rio de Janeiro</Text>
          </View>
          <Text style={s.eventArrow}>›</Text>
        </TouchableOpacity>

        <SectionTitle
          title="Últimas publicações"
          action="Explorar"
          onPress={() => setTab('Chat')}
        />

        <View style={s.postCard}>
          <View style={s.postHeader}>
            <View style={s.postAvatar}>
              <Text style={s.postAvatarText}>N</Text>
            </View>
            <View style={s.postAuthorInfo}>
              <Text style={s.postAuthor}>Nação Rubro-Negra</Text>
              <Text style={s.postTime}>Comunidade • há 12 min</Text>
            </View>
            <Text style={s.postMenu}>•••</Text>
          </View>
          <Text style={s.postTitle}>Dia de jogo é dia de fazer história! 🔴⚫</Text>
          <Text style={s.postBody}>
            Quem vai estar presente hoje? Vamos mostrar a força da nossa
            torcida e apoiar até o último minuto!
          </Text>
          <View style={s.postTags}>
            <Text style={s.postTag}>#Mengão</Text>
            <Text style={s.postTag}>#NossaTorcida</Text>
          </View>
          <View style={s.postDivider} />
          <View style={s.postActions}>
            <TouchableOpacity
              style={s.postAction}
              onPress={() => toggleLike('post1')}
            >
              <Text style={[s.actionText, liked.includes('post1') && s.liked]}>
                {liked.includes('post1') ? '♥ Curtido' : '♡ Curtir'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={s.postAction}
              onPress={() => setTab('Chat')}
            >
              <Text style={s.actionText}>▢ Comentar</Text>
            </TouchableOpacity>
            <TouchableOpacity style={s.postAction}>
              <Text style={s.actionText}>↗ Compartilhar</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={s.postCard}>
          <View style={s.postHeader}>
            <View style={[s.postAvatar, { backgroundColor: '#28283B' }]}>
              <Text style={s.postAvatarText}>T+</Text>
            </View>
            <View style={s.postAuthorInfo}>
              <Text style={s.postAuthor}>TORCIDA+ Comunidade</Text>
              <Text style={s.postTime}>Aviso da comunidade</Text>
            </View>
          </View>
          <Text style={s.postTitle}>Sua próxima caravana começa aqui 🚌</Text>
          <Text style={s.postBody}>
            Encontre viagens organizadas, combine encontros e acompanhe os
            próximos eventos da sua comunidade.
          </Text>
          <TouchableOpacity
            style={s.outlineButton}
            onPress={() => setTab('Eventos')}
          >
            <Text style={s.outlineButtonText}>ENCONTRAR EVENTOS</Text>
          </TouchableOpacity>
        </View>
      </>
    );
  }

  function Torcidas() {
    return (
      <>
        <Text style={s.pageTitle}>Comunidades</Text>
        <Text style={s.pageSubtitle}>
          Encontre sua galera e participe da paixão.
        </Text>
        {communities.map((team) => (
          <View key={team.name} style={s.listCard}>
            <View style={s.teamBadge}>
              <Text style={s.teamEmoji}>{team.emoji}</Text>
            </View>
            <View style={s.listInfo}>
              <Text style={s.listTitle}>{team.name}</Text>
              <Text style={s.listSubtitle}>{team.members} membros</Text>
            </View>
            <TouchableOpacity
              style={[
                s.smallButton,
                joined.includes(team.name) && s.joinedButton,
              ]}
              onPress={() => toggleJoin(team.name)}
            >
              <Text style={s.smallButtonText}>
                {joined.includes(team.name) ? 'Participando' : 'Participar'}
              </Text>
            </TouchableOpacity>
          </View>
        ))}
        <Text style={s.helperText}>
          Demonstração visual: a participação ainda não é salva em um servidor.
        </Text>
      </>
    );
  }

  function Events() {
    return (
      <>
        <Text style={s.pageTitle}>Eventos</Text>
        <Text style={s.pageSubtitle}>
          Jogos, encontros, reuniões e caravanas.
        </Text>
        {[
          { day: '08', month: 'NOV', title: 'Pré-jogo da torcida', detail: '16:00 • Rio de Janeiro' },
          { day: '11', month: 'NOV', title: 'Reunião da comunidade', detail: '19:00 • Reunião presencial' },
          { day: '15', month: 'NOV', title: 'Caravana para o estádio', detail: '14:00 • Saída a confirmar' },
        ].map((event) => (
          <View key={event.title} style={s.eventListCard}>
            <View style={s.eventDate}>
              <Text style={s.eventDay}>{event.day}</Text>
              <Text style={s.eventMonth}>{event.month}</Text>
            </View>
            <View style={s.eventInfo}>
              <Text style={s.eventTitle}>{event.title}</Text>
              <Text style={s.eventDetail}>{event.detail}</Text>
              <Text style={s.eventCategory}>EVENTO DEMONSTRATIVO</Text>
            </View>
          </View>
        ))}
      </>
    );
  }

  function Store() {
    return (
      <>
        <Text style={s.pageTitle}>Loja da torcida</Text>
        <Text style={s.pageSubtitle}>
          Produtos para vestir as cores da sua paixão.
        </Text>
        <View style={s.storeBanner}>
          <Text style={s.storeBannerSmall}>MOSTRE SUA PAIXÃO</Text>
          <Text style={s.storeBannerTitle}>Sua torcida.{'\n'}Seu estilo.</Text>
          <Text style={s.storeBannerDescription}>
            Camisas, acessórios e artigos personalizados.
          </Text>
        </View>
        {[
          { emoji: '👕', title: 'Camisa da torcida', price: 'Preço a consultar' },
          { emoji: '🧢', title: 'Boné personalizado', price: 'Preço a consultar' },
          { emoji: '🧣', title: 'Cachecol da torcida', price: 'Preço a consultar' },
        ].map((product) => (
          <View key={product.title} style={s.productCard}>
            <View style={s.productEmojiBox}>
              <Text style={s.productEmoji}>{product.emoji}</Text>
            </View>
            <View style={s.listInfo}>
              <Text style={s.listTitle}>{product.title}</Text>
              <Text style={s.listSubtitle}>{product.price}</Text>
            </View>
            <Text style={s.productArrow}>›</Text>
          </View>
        ))}
        <Text style={s.helperText}>
          Os produtos são ilustrativos. Não há venda ou pagamento ativo nesta versão.
        </Text>
      </>
    );
  }

  function Profile() {
    return (
      <>
        <Text style={s.pageTitle}>Meu perfil</Text>
        <View style={s.profileCard}>
          <View style={s.profileAvatar}>
            <Text style={s.profileAvatarText}>T+</Text>
          </View>
          <Text style={s.profileName}>Torcedor</Text>
          <Text style={s.profileSubtitle}>Faça parte dessa paixão.</Text>
          <TouchableOpacity
            style={s.primaryButton}
            onPress={() => setTab('Início')}
          >
            <Text style={s.primaryButtonText}>EXPLORAR TORCIDA</Text>
          </TouchableOpacity>
        </View>
        {[
          ['♧', 'Minhas comunidades'],
          ['▦', 'Meus eventos'],
          ['▣', 'Minhas compras'],
          ['♙', 'Dados pessoais'],
          ['⚙', 'Configurações'],
          ['?', 'Ajuda e suporte'],
        ].map(([icon, label]) => (
          <TouchableOpacity key={label} style={s.profileMenu}>
            <Text style={s.profileMenuIcon}>{icon}</Text>
            <Text style={s.profileMenuLabel}>{label}</Text>
            <Text style={s.productArrow}>›</Text>
          </TouchableOpacity>
        ))}
        <Text style={s.helperText}>
          O cadastro e a autenticação serão conectados ao backend em uma próxima etapa.
        </Text>
      </>
    );
  }

  function Chat() {
    return (
      <>
        <Text style={s.pageTitle}>Chat da torcida</Text>
        <Text style={s.pageSubtitle}>
          Fique perto da sua comunidade.
        </Text>
        <View style={s.emptyCard}>
          <Text style={s.emptyIcon}>☏</Text>
          <Text style={s.listTitle}>Sua torcida está esperando</Text>
          <Text style={s.emptyDescription}>
            Aqui ficarão as conversas, os grupos e os comunicados oficiais.
          </Text>
          <Text style={s.helperText}>
            O chat em tempo real ainda precisa ser conectado ao servidor.
          </Text>
        </View>
      </>
    );
  }

  return (
    <SafeAreaView style={s.safe}>
      <StatusBar barStyle="light-content" />
      <Header />

      <ScrollView
        key={tab}
        style={s.scroll}
        contentContainerStyle={s.content}
        showsVerticalScrollIndicator={false}
      >
        {tab === 'Início' && <Home />}
        {tab === 'Torcidas' && <Torcidas />}
        {tab === 'Eventos' && <Events />}
        {tab === 'Loja' && <Store />}
        {tab === 'Perfil' && <Profile />}
        {tab === 'Chat' && <Chat />}
      </ScrollView>

      <View style={s.nav}>
        {tabs.map((item) => {
          const active = tab === item.name;
          return (
            <TouchableOpacity
              key={item.name}
              style={s.navItem}
              onPress={() => setTab(item.name)}
            >
              <Text style={[s.navIcon, active && s.navIconActive]}>
                {item.icon}
              </Text>
              <Text style={[s.navText, active && s.navTextActive]}>
                {item.name}
              </Text>
              {active && <View style={s.navIndicator} />}
            </TouchableOpacity>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: BG },
  header: {
    minHeight: 70,
    paddingHorizontal: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
  },
  logo: { color: '#FFF', fontSize: 25, fontWeight: '900', letterSpacing: -1 },
  tagline: { color: MUTED, fontSize: 8, letterSpacing: 2.5, marginTop: 2 },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  notification: {
    width: 38, height: 38, borderRadius: 13,
    backgroundColor: CARD, alignItems: 'center', justifyContent: 'center',
  },
  notificationIcon: { color: '#FFF', fontSize: 21 },
  notificationDot: {
    position: 'absolute', top: 7, right: 7,
    width: 7, height: 7, borderRadius: 4, backgroundColor: RED,
  },
  avatar: {
    width: 40, height: 40, borderRadius: 14,
    backgroundColor: RED, alignItems: 'center', justifyContent: 'center',
  },
  avatarText: { color: '#FFF', fontSize: 15, fontWeight: '900' },
  scroll: { flex: 1 },
  content: { padding: 16, paddingBottom: 28 },
  welcome: {
    backgroundColor: '#151216', borderRadius: 22, padding: 20,
    borderWidth: 1, borderColor: '#392027', marginBottom: 26,
  },
  liveBadge: {
    alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#302027', paddingHorizontal: 10, paddingVertical: 7,
    borderRadius: 20,
  },
  liveDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: RED, marginRight: 7 },
  liveText: { color: '#F6B7C0', fontSize: 9, fontWeight: '900', letterSpacing: 1 },
  heroTitle: { color: '#FFF', fontSize: 29, fontWeight: '900', lineHeight: 36, marginTop: 20 },
  heroDescription: { color: '#C5C0C6', fontSize: 13, lineHeight: 21, marginTop: 12 },
  primaryButton: {
    backgroundColor: RED, minHeight: 48, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center', paddingHorizontal: 14, marginTop: 18,
  },
  primaryButtonText: { color: '#FFF', fontSize: 11, fontWeight: '900', letterSpacing: 0.5 },
  heroFooter: { flexDirection: 'row', alignItems: 'center', marginTop: 18 },
  avatarStack: { flexDirection: 'row', marginRight: 9 },
  stackEmoji: {
    fontSize: 14, backgroundColor: '#29232A', overflow: 'hidden',
    borderRadius: 20, padding: 5, marginRight: -3,
  },
  heroFooterText: { color: MUTED, fontSize: 10, flexShrink: 1 },
  sectionHeader: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 14, marginTop: 2,
  },
  sectionTitle: { color: '#FFF', fontSize: 18, fontWeight: '900' },
  seeAll: { color: RED, fontSize: 11, fontWeight: '800' },
  communityScroll: { marginBottom: 25, marginRight: -16 },
  communityCard: {
    width: 122, backgroundColor: CARD, borderRadius: 16, padding: 13,
    marginRight: 10, borderWidth: 1, borderColor: BORDER,
  },
  teamBadge: {
    width: 45, height: 45, borderRadius: 15, backgroundColor: '#29242B',
    alignItems: 'center', justifyContent: 'center', marginBottom: 10,
  },
  teamEmoji: { fontSize: 23 },
  teamName: { color: '#FFF', fontSize: 12, fontWeight: '900' },
  memberCount: { color: MUTED, fontSize: 9, marginTop: 5 },
  eventCard: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: CARD,
    borderRadius: 16, padding: 13, borderWidth: 1, borderColor: BORDER, marginBottom: 26,
  },
  eventDate: {
    width: 49, height: 55, borderRadius: 12, backgroundColor: '#302027',
    alignItems: 'center', justifyContent: 'center', marginRight: 12,
  },
  eventDay: { color: '#FFF', fontSize: 20, fontWeight: '900' },
  eventMonth: { color: '#F69BA7', fontSize: 9, fontWeight: '900', marginTop: 1 },
  eventInfo: { flex: 1 },
  eventCategory: { color: RED, fontSize: 8, fontWeight: '900', letterSpacing: 0.8 },
  eventTitle: { color: '#FFF', fontSize: 13, fontWeight: '800', marginTop: 5 },
  eventDetail: { color: MUTED, fontSize: 10, marginTop: 6 },
  eventArrow: { color: '#FFF', fontSize: 25, paddingLeft: 8 },
  postCard: {
    backgroundColor: CARD, borderRadius: 17, padding: 15,
    borderWidth: 1, borderColor: BORDER, marginBottom: 14,
  },
  postHeader: { flexDirection: 'row', alignItems: 'center' },
  postAvatar: {
    width: 40, height: 40, borderRadius: 14, backgroundColor: '#4A1721',
    alignItems: 'center', justifyContent: 'center', marginRight: 10,
  },
  postAvatarText: { color: '#FFF', fontSize: 15, fontWeight: '900' },
  postAuthorInfo: { flex: 1 },
  postAuthor: { color: '#FFF', fontSize: 12, fontWeight: '800' },
  postTime: { color: MUTED, fontSize: 10, marginTop: 4 },
  postMenu: { color: MUTED, fontSize: 18 },
  postTitle: { color: '#FFF', fontSize: 15, lineHeight: 21, fontWeight: '900', marginTop: 15 },
  postBody: { color: '#C4C4CC', fontSize: 12, lineHeight: 20, marginTop: 8 },
  postTags: { flexDirection: 'row', marginTop: 10 },
  postTag: { color: '#FF7180', fontSize: 11, fontWeight: '700', marginRight: 10 },
  postDivider: { height: 1, backgroundColor: BORDER, marginTop: 15 },
  postActions: { flexDirection: 'row', justifyContent: 'space-between', paddingTop: 13 },
  postAction: { paddingVertical: 3, paddingRight: 5 },
  actionText: { color: MUTED, fontSize: 10, fontWeight: '700' },
  liked: { color: RED },
  outlineButton: {
    borderWidth: 1, borderColor: RED, borderRadius: 10, padding: 12,
    alignItems: 'center', marginTop: 15,
  },
  outlineButtonText: { color: '#FF6676', fontSize: 10, fontWeight: '900' },
  pageTitle: { color: '#FFF', fontSize: 27, fontWeight: '900', marginTop: 8 },
  pageSubtitle: { color: MUTED, fontSize: 13, lineHeight: 20, marginTop: 7, marginBottom: 23 },
  listCard: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: CARD,
    borderRadius: 16, padding: 13, marginBottom: 11, borderWidth: 1, borderColor: BORDER,
  },
  listInfo: { flex: 1 },
  listTitle: { color: '#FFF', fontSize: 13, fontWeight: '800' },
  listSubtitle: { color: MUTED, fontSize: 10, marginTop: 5 },
  smallButton: { backgroundColor: RED, borderRadius: 9, paddingHorizontal: 11, paddingVertical: 10 },
  joinedButton: { backgroundColor: '#303036' },
  smallButtonText: { color: '#FFF', fontSize: 10, fontWeight: '800' },
  helperText: { color: '#777781', fontSize: 10, lineHeight: 16, marginTop: 16, marginBottom: 12 },
  eventListCard: {
    flexDirection: 'row', backgroundColor: CARD, padding: 14, borderRadius: 16,
    borderWidth: 1, borderColor: BORDER, marginBottom: 12,
  },
  storeBanner: {
    backgroundColor: '#25141A', borderWidth: 1, borderColor: '#4A202A',
    borderRadius: 20, padding: 20, marginBottom: 23,
  },
  storeBannerSmall: { color: '#FF8A98', fontSize: 9, fontWeight: '900', letterSpacing: 1.5 },
  storeBannerTitle: { color: '#FFF', fontSize: 28, fontWeight: '900', marginTop: 10, lineHeight: 33 },
  storeBannerDescription: { color: '#D0C1C5', fontSize: 12, lineHeight: 19, marginTop: 8 },
  productCard: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: CARD,
    borderRadius: 15, padding: 12, marginBottom: 11, borderWidth: 1, borderColor: BORDER,
  },
  productEmojiBox: {
    width: 53, height: 53, backgroundColor: '#29232A',
    borderRadius: 13, alignItems: 'center', justifyContent: 'center', marginRight: 12,
  },
  productEmoji: { fontSize: 27 },
  productArrow: { color: MUTED, fontSize: 24, paddingHorizontal: 5 },
  profileCard: {
    backgroundColor: CARD, alignItems: 'center', padding: 23, borderRadius: 19,
    borderWidth: 1, borderColor: BORDER, marginBottom: 20,
  },
  profileAvatar: {
    width: 78, height: 78, borderRadius: 28, backgroundColor: RED,
    alignItems: 'center', justifyContent: 'center',
  },
  profileAvatarText: { color: '#FFF', fontSize: 28, fontWeight: '900' },
  profileName: { color: '#FFF', fontSize: 18, fontWeight: '900', marginTop: 13 },
  profileSubtitle: { color: MUTED, fontSize: 12, marginTop: 5 },
  profileMenu: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: CARD,
    padding: 15, borderRadius: 13, marginBottom: 8,
  },
  profileMenuIcon: { color: RED, width: 32, fontSize: 18 },
  profileMenuLabel: { color: '#FFF', fontSize: 12, fontWeight: '700', flex: 1 },
  emptyCard: {
    backgroundColor: CARD, padding: 24, borderRadius: 18,
    alignItems: 'center', borderWidth: 1, borderColor: BORDER, marginTop: 10,
  },
  emptyIcon: { color: RED, fontSize: 45, marginBottom: 15 },
  emptyDescription: { color: MUTED, fontSize: 12, lineHeight: 20, textAlign: 'center', marginTop: 10 },
  nav: {
    minHeight: 66, flexDirection: 'row', backgroundColor: '#111114',
    borderTopWidth: 1, borderTopColor: BORDER, paddingBottom: 3,
  },
  navItem: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 8 },
  navIcon: { color: '#85858F', fontSize: 22 },
  navIconActive: { color: RED, fontWeight: '900' },
  navText: { color: '#85858F', fontSize: 9, marginTop: 4 },
  navTextActive: { color: RED, fontWeight: '900' },
  navIndicator: { width: 15, height: 2, backgroundColor: RED, borderRadius: 2, marginTop: 4 },
});
