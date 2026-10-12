"""DarkFlow SaaS Studio Controller

Dedicated API endpoints for Dark Channels & Science Shorts automation.
Provides preset hooks, voice settings, subtitle templates, system health,
and direct settings management.
"""

from typing import Any, Dict, List, Optional
from fastapi import BackgroundTasks, Depends, File, Query, Request, UploadFile
from pydantic import BaseModel, Field

from app.config import config
from app.controllers import base
from app.controllers.v1.base import new_router
from app.services import state as sm
from app.utils import utils

router = new_router(dependencies=[Depends(base.verify_token)])


SCIENCE_PRESETS = [
    {
        "id": "black_holes",
        "category": "Espaço & Astrofísica",
        "icon": "🌌",
        "title": "O que Acontece se Você Cair em um Buraco Negro?",
        "hook": "Se você caísse em um buraco negro agora, seu corpo sofreria um fenômeno chamado espaguetificação.",
        "script": "Se você caísse em um buraco negro de massa estelar, a gravidade nos seus pés seria trilhões de vezes mais intensa do que na sua cabeça. Esse fenômeno brutal, conhecido pela astrofísica como espaguetificação, esticaria seu corpo como um fio fino antes mesmo de cruzar o ponto de não retorno. Mas a verdadeira distorção acontece no horizonte de eventos. Para um observador externo distante, sua imagem pareceria congelar no tempo, ficando avermelhada até desaparecer na escuridão eterna. Para você, no entanto, o tempo continuaria fluindo, e você veria toda a luz e o futuro do cosmos passarem acelerados diante dos seus olhos em questão de instantes. No centro desse abismo reside a singularidade: um ponto de densidade infinita onde as leis da física que conhecemos deixam de existir.",
        "terms": ["black hole space galaxy cosmic event horizon cinematic 4k", "universe stars galaxy astrophysics deep space"],
        "video_tags": ["black hole cinematic", "accretion disk 4k", "galaxy stars deep space", "event horizon simulation"],
        "image_tags": ["Hubble black hole", "James Webb deep space", "supermassive black hole visualization", "galaxy cluster NASA"],
        "gif_tags": ["black hole accretion disk gif", "gravitational lensing animation", "neutron star rotating gif"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "viral_yellow",
    },
    {
        "id": "fermi_paradox",
        "category": "Espaço & Astrofísica",
        "icon": "👽",
        "title": "O Paradoxo de Fermi e a Hipótese da Floresta Sombria",
        "hook": "Existem centenas de bilhões de planetas na nossa galáxia. Por que o universo está em silêncio absoluto?",
        "script": "O universo observável contém mais de duzentos bilhões de galáxias e trilhões de planetas potencialmente habitáveis. Pela probabilidade estatística, civilizações alienígenas deveriam ter surgido milhões de anos antes da nossa e colonizado as estrelas. Essa discrepância arrepiante é o que os astrônomos chamam de Paradoxo de Fermi. Uma das soluções mais aterrorizantes propostas pela teoria dos jogos é a Hipótese da Floresta Sombria. Imagine o cosmos como uma floresta escura à noite, onde cada civilização é um caçador armado e invisível. Nesse cenário cósmico, qualquer civilização que emita sinais de rádio ou revele sua localização pode ser instantaneamente aniquilada por vizinhos mais avançados como medida preventiva. Talvez o silêncio do espaço não signifique ausência de vida, mas sim que todos estão quietos com medo do que espreita nas sombras.",
        "terms": ["deep space stars telescope alien cosmos radio telescope milky way 4k", "nebula constellation galaxy universe astronomy"],
        "video_tags": ["radio telescope night sky", "milky way galaxy timelapse", "deep space stars cinematic", "cosmos planet aerial"],
        "image_tags": ["SETI Allen Telescope Array", "James Webb cosmic deep field", "Arecibo observatory radio telescope", "Andromeda galaxy high resolution"],
        "gif_tags": ["pulsar rotating gif", "radio telescope rotating timelapse", "solar system simulation gif"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "viral_yellow",
    },
    {
        "id": "james_webb",
        "category": "Espaço & Astrofísica",
        "icon": "🔭",
        "title": "O Telescópio James Webb e as Galáxias Proibidas",
        "hook": "O telescópio James Webb acaba de fotografar estruturas que a cosmologia dizia serem impossíveis.",
        "script": "A um milhão e meio de quilômetros da Terra, o espelho banhado a ouro do telescópio espacial James Webb está desafiando tudo o que os astrofísicos achavam que sabiam sobre a origem do universo. Ao capturar a luz infravermelha emitida há mais de treze bilhões de anos, o observatório revelou galáxias maciças e hiperluminosas existindo apenas algumas centenas de milhões de anos após o Big Bang. De acordo com o modelo cosmológico padrão, essas estruturas cósmicas simplesmente não deveriam ter tido tempo suficiente para acumular tanta matéria estelar. Para os cientistas, isso sugere duas possibilidades chocantes: ou buracos negros primordiais gigantescos já existiam antes mesmo das primeiras estrelas, ou a nossa compreensão sobre a idade e a velocidade de expansão do tecido do cosmos precisa ser completamente reescrita.",
        "terms": ["James Webb space telescope galaxy deep space gold mirrors NASA 4k", "infrared astronomy nebula stellar nursery cosmos"],
        "video_tags": ["space telescope orbit 4k", "galaxy cluster james webb", "astronomy deep field 4k", "stars forming nebula"],
        "image_tags": ["James Webb primary mirror gold", "Carina Nebula cosmic cliffs", "SMACS 0723 deep field", "Pillars of Creation infrared"],
        "gif_tags": ["space telescope deployment animation", "spiral galaxy rotation gif", "supernova explosion animation"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "electric_cyan",
    },
    {
        "id": "ocean_abyss",
        "category": "Abismo Oceânico & Mistérios",
        "icon": "🌊",
        "title": "O Ponto Mais Profundo do Oceano Guarda um Segredo",
        "hook": "Sabia que nós conhecemos mais sobre a superfície da Lua do que sobre as profundezas do nosso próprio oceano?",
        "script": "Nós conhecemos com mais detalhes a superfície da Lua do que as profundezas do nosso próprio oceano. Na Fossa das Marianas, a quase onze mil metros abaixo da superfície, a pressão sobre qualquer corpo equivale ao peso de cinquenta aviões comerciais concentrados. Nesse ambiente hostil e congelante, onde a luz solar nunca penetrou em bilhões de anos, a vida não apenas sobrevive, mas prospera de maneiras surpreendentes. Criaturas translúcidas, peixes sem olhos e organismos bioluminescentes utilizam processos químicos únicos em vez de fotossíntese. O que mais impressiona os biólogos é que muitas dessas espécies parecem biologicamente imunes ao envelhecimento tradicional. Enquanto exploramos galáxias distantes em busca de vida alienígena, um ecossistema inteiramente alienígena já existe bem aqui, silencioso no fundo da Terra.",
        "terms": ["deep ocean abyss underwater Mariana Trench bioluminescent creature 4k", "dark ocean underwater mysterious sea"],
        "video_tags": ["deep ocean trench 4k", "submersible underwater dark", "bioluminescent sea creatures", "hydrothermal vent ocean floor"],
        "image_tags": ["Mariana Trench bathyscaphe Trieste", "deep sea anglerfish bioluminescence", "NOAA ocean floor benthic organisms", "submarine underwater high resolution"],
        "gif_tags": ["deep sea jellyfish pulse gif", "bioluminescent ocean wave gif", "submarine diving underwater animation"],
        "voice": "pt-BR-FranciscaNeural",
        "voice_rate": 1.12,
        "style": "electric_cyan",
    },
    {
        "id": "bloop_sound",
        "category": "Abismo Oceânico & Mistérios",
        "icon": "🐋",
        "title": "O Mistério do Bloop e os Sons Inexplicáveis do Mar",
        "hook": "Em mil novecentos e noventa e sete, hidrofones militares detectaram um som no fundo do Pacífico que viajou cinco mil quilômetros.",
        "script": "Durante a Guerra Fria, uma rede ultra-sensível de hidrofones subaquáticos foi instalada pela marinha para rastrear submarinos nucleares. No entanto, em 1997, os sensores captaram um ruído de frequência ultrabaixa no fundo do oceano Pacífico Sul que se espalhou por mais de cinco mil quilômetros de distância. Batizado pelos oceanógrafos de Bloop, o som tinha uma assinatura acústica muito semelhante à de um animal orgânico vivo, porém com uma intensidade sonora várias vezes superior à da maior baleia azul já registrada na Terra. Embora relatórios posteriores da NOAA tenham atribuído o som à fratura maciça de geleiras na Antártida, o fenômeno reacendeu debates sobre o quanto da biosfera oceânica profunda permanece desconhecida pela humanidade. Mais de oitenta por cento das bacias oceânicas continuam sem nenhum mapeamento de alta resolução.",
        "terms": ["sonar ocean hydrophone underwater abyss waves ice shelf cracking 4k", "deep sea acoustic radar dark waters whale underwater"],
        "video_tags": ["ocean waves stormy dark 4k", "underwater blue abyss rays", "iceberg underwater glacier", "sonar radar screen submarine"],
        "image_tags": ["NOAA research vessel acoustic hydrophone", "Antarctic ice shelf calving ocean", "bathymetric ocean floor map", "deep ocean trench darkness"],
        "gif_tags": ["ocean sonar pulse radar gif", "iceberg calving ocean loop", "whale swimming deep ocean gif"],
        "voice": "pt-BR-FranciscaNeural",
        "voice_rate": 1.12,
        "style": "electric_cyan",
    },
    {
        "id": "brain_reality",
        "category": "Neurociência & Psicologia",
        "icon": "🧠",
        "title": "Seu Cérebro Apaga Memórias Toda Vez que Você Pisca",
        "hook": "Você pisca cerca de vinte mil vezes por dia, mas nunca percebe a escuridão.",
        "script": "Você pisca cerca de vinte mil vezes por dia, mas em nenhum momento enxerga a escuridão. Isso acontece porque o cérebro humano literalmente desliga os seus centros de percepção visual milissegundos antes da pálpebra se mover e reconstrói artificialmente uma ilusão de continuidade. Na prática, você passa quase uma hora de cada dia acordado completamente cego sem nem sequer notar. Mas o mistério da mente humana é ainda mais profundo. Durante esse breve apagão inconsciente, redes neurais operam em segundo plano filtrando estímulos secundários e descartando dados considerados irrelevantes para a sua sobrevivência imediata. O que você chama de realidade não é uma transmissão ao vivo do mundo exterior, mas sim uma simulação editada e controlada pelo seu cérebro para manter sua sanidade intacta.",
        "terms": ["human brain neurons synapses glowing firing consciousness 4k", "eye blink macro iris human biology visual"],
        "video_tags": ["neurons firing electrical synapse 4k", "macro human iris eye slow motion", "brain MRI scanning medical", "consciousness neural network concept"],
        "image_tags": ["synapse electron microscope neural pathway", "human brain anatomy cross section", "fMRI brain mapping neuroscience", "retina rods and cones microscopic"],
        "gif_tags": ["neural impulse synapse firing gif", "pupil dilation iris macro loop", "brain wave EEG electrical activity animation"],
        "voice": "pt-BR-ThalitaMultilingualNeural",
        "voice_rate": 1.15,
        "style": "cyber_green",
    },
    {
        "id": "dunning_kruger",
        "category": "Neurociência & Psicologia",
        "icon": "🎭",
        "title": "O Efeito Dunning-Kruger e a Armadilha da Certeza",
        "hook": "Quanto menos uma pessoa sabe sobre um assunto, mais ela tem absoluta certeza de que domina tudo.",
        "script": "Em 1999, psicólogos da Universidade de Cornell descobriram um viés cognitivo fascinante que afeta praticamente todos os seres humanos: o Efeito Dunning-Kruger. Quando alguém possui apenas conhecimentos superficiais sobre uma área complexa, seu cérebro carece das ferramentas metacognitivas necessárias para avaliar o tamanho da própria ignorância. Como resultado, indivíduos inexperientes experimentam um pico artificial de autoconfiança, acreditando genuinamente estarem no topo da sabedoria. Por outro lado, à medida que uma pessoa estuda profundamente e domina uma disciplina, ela percebe a vasta complexidade do campo e tende a subestimar a própria capacidade intelectual. A verdadeira sabedoria não se manifesta na convicção inabalável de ter todas as respostas, mas sim na coragem de questionar as próprias certezas e reconhecer os limites do saber.",
        "terms": ["thinking chess mind psychological cognitive bias human face contemplation 4k", "pensive scholar books library laboratory research philosophy"],
        "video_tags": ["chess board move cinematic 4k", "contemplative silhouette human thinking", "library old books scholar study", "reflection glass human expression"],
        "image_tags": ["Auguste Rodin The Thinker sculpture", "ancient Greek philosophers fresco Athens", "psychology experiment laboratory historical", "chess grandmaster board tension"],
        "gif_tags": ["chess king falling slow motion gif", "optical illusion rotating gears animation", "human eye focus mental concentration gif"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.12,
        "style": "viral_yellow",
    },
    {
        "id": "overton_window",
        "category": "Neurociência & Psicologia",
        "icon": "🚪",
        "title": "A Janela de Overton: Como Ideias Proibidas Viram Lei",
        "hook": "Existe uma técnica psicológica usada para transformar o que é impensável em algo comum na sociedade.",
        "script": "Já percebeu como propostas que antes pareciam inconcebíveis de repente se tornam políticas públicas obrigatórias? Esse fenômeno é governado pela Janela de Overton, um modelo que descreve a faixa de ideias toleradas pelo discurso público em um determinado momento histórico. A janela se desloca em seis estágios graduais: impensável, radical, aceitável, sensato, popular e finalmente formalizado em legislação. Governos, grupos de pressão e veículos de mídia utilizam essa dinâmica testando narrativas extremas nas bordas do debate para normalizar tópicos intermediários. Quando a atenção coletiva se acostuma com o choque inicial, o centro de gravidade moral se move silenciosamente. Controlar quais pensamentos são permitidos no debate público é a forma mais refinada de influenciar civilizações inteiras sem disparar um único tiro.",
        "terms": ["media television news broadcast newspapers printing press politics debate 4k", "cables broadcasting control room camera broadcast studio"],
        "video_tags": ["news studio broadcast cameras 4k", "printing press newspapers rolling", "television screens wall glitch surveillance", "parliament speech debate podium"],
        "image_tags": ["vintage printing press Gutenberg era", "television broadcast control room 1970s", "newspaper headlines historical archive", "crowd assembly public forum square"],
        "gif_tags": ["television glitch static noise gif", "printing press cylinders rotating loop", "binary code data stream animation"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "pure_white",
    },
    {
        "id": "quantum_time",
        "category": "Física Quântica & Multiverso",
        "icon": "⚛️",
        "title": "O Tempo Passa Mais Rápido na Sua Cabeça do que nos Seus Pés",
        "hook": "A gravidade da Terra altera o fluxo do tempo, e Einstein provou isso.",
        "script": "A gravidade da Terra altera fisicamente o fluxo do tempo, e Albert Einstein provou isso com a teoria da relatividade geral. Como os seus pés estão mais próximos do centro de gravidade do planeta, o tempo passa ligeiramente mais devagar para eles do que para o seu cérebro. Para o corpo humano a diferença é imperceptível, na escala de frações de nanossegundos ao longo de uma vida inteira. Porém, para os satélites de navegação que orbitam a Terra a milhares de quilômetros de altitude, essa distorção temporal é uma questão de precisão matemática crítica. Se os relógios atômicos a bordo não fossem corrigidos diariamente para compensar essa diferença, os sistemas de GPS globais acumulariam um erro de mais de dez quilômetros a cada vinte e quatro horas.",
        "terms": ["quantum physics time relativity clock gravity distortion space 4k", "universe time dilation cosmos Einstein space physics"],
        "video_tags": ["atomic clock ticking gears 4k", "satellite orbiting earth space", "spacetime fabric gravity curvature 3d", "light speed relativity simulation"],
        "image_tags": ["atomic clock NIST laboratory", "GPS satellite constellation orbit", "Einstein relativity equations blackboard", "gravitational redshift astronomical data"],
        "gif_tags": ["spacetime curvature ball warping grid gif", "clock gears spinning macro loop", "satellite orbital mechanics earth animation"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "viral_yellow",
    },
    {
        "id": "double_slit",
        "category": "Física Quântica & Multiverso",
        "icon": "✨",
        "title": "O Experimento da Dupla Fenda e o Mistério do Observador",
        "hook": "Uma partícula quântica sabe quando você está olhando para ela e muda de comportamento.",
        "script": "O Experimento da Dupla Fenda é considerado o ensaio científico mais desconcertante da história da humanidade. Quando fótons ou elétrons são disparados individualmente contra uma barreira com duas fendas, eles colidem com a tela de detecção desenhando um padrão de interferência ondulatório, como se cada partícula passasse pelas duas fendas simultaneamente. No entanto, quando os físicos instalaram detectores ultraprecisos para descobrir por qual abertura a partícula realmente passava, algo inacreditável aconteceu: a função de onda colapsou instantaneamente e o elétron voltou a se comportar como uma simples partícula sólida. O mero ato de observar a trajetória mudou o resultado do mundo físico. Isso levou pioneiros como Niels Bohr e Werner Heisenberg a sugerirem que a realidade objetiva não existe até que seja medida por um observador consciente.",
        "terms": ["quantum physics laser light interference waves particles laboratory 4k", "electron microscope laboratory optical beam physics"],
        "video_tags": ["laser beam dark laboratory optics 4k", "wave interference ripples water slow motion", "electron beam microscopic particle", "particle accelerator physics tunnel"],
        "image_tags": ["double slit experiment interference fringes diagram", "CERN Large Hadron Collider detector", "optical laser bench prism refraction", "quantum mechanics wave equation historical"],
        "gif_tags": ["double slit wave interference pattern simulation gif", "quantum wave packet dispersion loop", "laser beam diffraction animated gif"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.14,
        "style": "electric_cyan",
    },
    {
        "id": "quantum_entanglement",
        "category": "Física Quântica & Multiverso",
        "icon": "🔗",
        "title": "Entrelaçamento Quântico e a Ação Fantasmagórica",
        "hook": "Duas partículas conectadas podem se comunicar instantaneamente mesmo nos lados opostos do universo.",
        "script": "Albert Einstein chamou o entrelaçamento quântico de 'ação fantasmagórica à distância' porque o fenômeno parecia violar o limite fundamental da velocidade da luz. Quando duas partículas entram emaranhadas em um mesmo estado quântico, qualquer alteração no spin ou na polarização de uma delas determina instantaneamente o estado da outra, não importa se estão a centímetros de distância ou em galáxias diametralmente opostas. Não há troca de sinal físico viajando pelo espaço; a conexão é imediata e atemporal. Em 2022, o Prêmio Nobel de Física confirmou experimentalmente que o nosso universo não é localmente real, ou seja, as propriedades dos objetos não têm valores pré-determinados antes da observação. Esse princípio hoje serve como alicerce para computadores quânticos ultravelozes e redes criptográficas inquebráveis.",
        "terms": ["quantum entanglement connected particles glow fiber optic laser 4k", "supercomputer quantum processor glowing blue cryostat"],
        "video_tags": ["quantum computer dilution refrigerator golden 4k", "fiber optic cables glowing light pulse", "particle connection glowing energy line", "subatomic interaction visual simulation"],
        "image_tags": ["IBM quantum computer golden chandelier cryostat", "photonic quantum chip laboratory", "Bell inequality physics experiment diagram", "entangled photons laser table setup"],
        "gif_tags": ["entangled particles spin correlation animation", "quantum computing qubit superposition gif", "fiber optic data stream loop"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "electric_cyan",
    },
    {
        "id": "antikythera",
        "category": "Arqueologia & Civilizações Antigas",
        "icon": "🏛️",
        "title": "O Mecanismo de Anticítera: O Primeiro Computador da História",
        "hook": "Em 1901, mergulhadores gregos acharam uma máquina de engrenagens de mais de dois mil anos no fundo do mar.",
        "script": "Perto da ilha grega de Anticítera, a quarenta e cinco metros de profundidade, mergulhadores recolheram os destroços de um navio mercante romano naufragado no século I antes de Cristo. Entre estátuas de mármore e moedas de ouro, havia um pedaço de bronze corroído com inscrições misteriosas. Quando tomografias computadorizadas modernas escanearam o interior do objeto, revelaram trinta engrenagens de bronze em miniatura, diferenciais complexos e ponteiros astronômicos de alta precisão. O chamado Mecanismo de Anticítera era um computador analógico programado para prever as fases lunares, eclipses solares, as órbitas dos planetas conhecidos e o calendário dos Jogos Olímpicos. A sofisticação tecnológica contida nessa caixa grega era tão avançada que relógios mecânicos com engrenagens equivalentes só voltaram a ser construídos na Europa mil e quatrocentos anos depois.",
        "terms": ["ancient Greek artifact bronze gears Antikythera archaeological dive 4k", "museum Roman shipwreck underwater antiquities ancient history"],
        "video_tags": ["ancient Greek temple ruins aerial 4k", "bronze watch gears macro ticking", "archaeological excavation underwater dive", "museum artifact display lighting"],
        "image_tags": ["Antikythera mechanism National Archaeological Museum Athens", "bronze gear teeth fragment macro", "reconstruction 3d model Antikythera", "ancient Greek astrolabe brass antique"],
        "gif_tags": ["Antikythera mechanism 3d gear simulation gif", "ancient astrolabe rotating astronomy animation", "gear train mechanical movement loop"],
        "voice": "pt-BR-DuarteNeural",
        "voice_rate": 1.12,
        "style": "pure_white",
    },
    {
        "id": "heracleion_sunken",
        "category": "Arqueologia & Civilizações Antigas",
        "icon": "🔱",
        "title": "Thonis-Heracleion: A Metrópole Submersa no Nilo",
        "hook": "Por mais de dois mil anos, historiadores achavam que a cidade egípcia de Heracleion era apenas uma lenda mitológica.",
        "script": "Mencionada por historiadores clássicos como Heródoto e cantada por poetas da antiguidade, a cidade portuária de Thonis-Heracleion era a principal porta de entrada marítima do Egito dos Faraós. No entanto, por mais de dois mil anos nenhum arqueólogo encontrou sequer uma pedra de suas muralhas, levando a comunidade acadêmica a acreditar que a urbe era pura mitologia. Tudo mudou no ano 2000, quando o arqueólogo marinho Franck Goddio descobriu as ruínas colossais submersas a seis quilômetros da costa de Alexandria, cobertas por dez metros de água e sedimentos do Mediterrâneo. Um cataclismo geológico combinado com liquefação do solo e terremotos afundou templos gigantescos, estátuas faraônicas de granito de cinco metros de altura e dezenas de navios com tesouros intocados no leito marítimo.",
        "terms": ["underwater archaeology sunken city Egypt statues temple Mediterranean 4k", "pharaoh granite sculpture underwater scuba diving ruins"],
        "video_tags": ["underwater ruins scuba diving exploration 4k", "granite pharaoh statue underwater sand", "ancient Egyptian temple columns ruins", "Mediterranean sea aerial coastline"],
        "image_tags": ["Franck Goddio underwater discovery statue Hapi", "sunken Egyptian stele hieroglyphics underwater", "Alexandria harbour underwater archaeology", "ancient Egyptian gold coins treasures seabed"],
        "gif_tags": ["underwater diver flashlight ruins loop", "sand shifting over submerged statue animation", "ancient Alexandria port reconstruction gif"],
        "voice": "pt-BR-DuarteNeural",
        "voice_rate": 1.12,
        "style": "pure_white",
    },
    {
        "id": "fiat_money_illusion",
        "category": "Economia & Dinheiro",
        "icon": "💵",
        "title": "A Grande Ilusão da Moeda Fiduciária",
        "hook": "Você sabia que a maior parte do dinheiro que existe no mundo hoje não foi impressa por governos?",
        "script": "Ao contrário do que a maioria das pessoas acredita, os governos e casas da moeda imprimem menos de cinco por cento de todo o suprimento monetário em circulação. Mais de noventa e cinco por cento do capital existente em economias modernas é criado do nada por bancos comerciais através do sistema de reservas fracionárias toda vez que um empréstimo ou financiamento é concedido. O termo fiduciário vem do latim 'fiducia', que significa confiança mútua. As cédulas e os saldos eletrônicos nas contas bancárias não têm lastro em ouro, prata ou qualquer mercadoria física tangível; seu poder de compra repousa unicamente na fé coletiva de que o próximo cidadão aceitará a moeda. Quando um banco central inflaciona descontroladamente a base monetária, não é o valor das coisas que sobe, mas sim o poder de compra da moeda que evapora.",
        "terms": ["money printing currency dollar bills banking vault economy stock market 4k", "gold bullion bars reserve bank financial charts dark"],
        "video_tags": ["banknotes currency printing press rolling 4k", "gold bars stacked vault shiny", "stock exchange trading floor screen", "digital financial ticker numbers market"],
        "image_tags": ["Federal Reserve bank building Washington", "vintage bank vault heavy steel door open", "weimar republic hyperinflation wheelbarrow money", "gold bars 999 bullion depository"],
        "gif_tags": ["currency printing press continuous loop gif", "stock market candlestick chart ticking animation", "gold coin spinning loop"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "viral_yellow",
    },
    {
        "id": "tulip_mania",
        "category": "Economia & Dinheiro",
        "icon": "🌷",
        "title": "A Febre das Tulipas: A Primeira Bolha Financeira",
        "hook": "No século XVII, na Holanda, o bulbo de uma única flor chegou a valer mais do que uma mansão inteira com carruagem.",
        "script": "Durante a Era de Ouro holandesa na década de 1630, um fenômeno de especulação coletiva sem precedentes tomou conta de Amsterdã: a Tulipa Mania. Introduzida a partir do Império Otomano, a flor com pétalas listradas tornou-se o maior símbolo de status da nobreza europeia. Em poucos meses, os preços dos bulbos dispararam em uma espiral frenética impulsionada pelos primeiros contratos de derivativos futuros da história. No ápice da euforia, em 1637, um único exemplar da rara tulipa 'Semper Augustus' foi negociado pelo valor equivalente a doze acres de terra fértil ou a uma mansão com criados. Mas quando os primeiros compradores se recusaram a honrar os lances em um leilão de rotina em Haarlem, o pânico varreu a economia holandesa. Em menos de duas semanas, o mercado colapsou noventa e nove por cento, arruinando investidores e deixando apenas papel sem valor.",
        "terms": ["Amsterdam canal historical Dutch golden age tulip flower market trading 4k", "17th century painting stock exchange merchants historical"],
        "video_tags": ["Amsterdam canals historic brick buildings 4k", "tulip flower blooming macro field", "vintage oil painting Dutch master museum", "gold coins pouch antique merchant table"],
        "image_tags": ["Semper Augustus tulip watercolor painting 1637", "Amsterdam stock exchange historical engraving", "Dutch golden age merchant portrait museum", "tulip bulb market historical document"],
        "gif_tags": ["tulip blooming timelapse gif", "candlestick crash chart animation", "historic sailing ship waves loop"],
        "voice": "pt-BR-DuarteNeural",
        "voice_rate": 1.12,
        "style": "viral_yellow",
    },
    {
        "id": "yellowstone_supervolcano",
        "category": "Geologia & Catástrofes",
        "icon": "🌋",
        "title": "O Supervulcão de Yellowstone e o Inverno Global",
        "hook": "Sob as fontes termais do parque de Yellowstone dorme uma câmara de magma capaz de cobrir um continente de cinzas.",
        "script": "Sob a paisagem deslumbrante de florestas e gêiseres do Parque Nacional de Yellowstone encontra-se uma das maiores caldeiras vulcânicas ativas do planeta Terra. Com cerca de setenta quilômetros de diâmetro, essa câmara subterrânea abriga dezenas de milhares de quilômetros cúbicos de rocha derretida e gases sob pressão extrema. Geólogos descobriram que o supervulcão entrou em erupção catastrófica em três ocasiões nos últimos dois milhões de anos, em intervalos aproximados de seiscentos a setecentos mil anos. Uma nova erupção no Índice de Explosividade Vulcânica nível oito lançaria milhares de quilômetros cúbicos de cinzas tóxicas na estratosfera, bloqueando a radiação solar por anos. A temperatura média global cairia drasticamente, desencadeando um inverno vulcânico que devastaria as safras agrícolas e ameaçaria o abastecimento alimentar da civilização.",
        "terms": ["volcano eruption lava magma Yellowstone geyser thermal geothermal aerial 4k", "volcanic ash cloud caldera geology dark nature"],
        "video_tags": ["volcano eruption lava fountain slow motion 4k", "Yellowstone Grand Prismatic spring aerial", "geothermal geyser eruption steam smoke", "volcanic ash cloud lightning thunderstorm"],
        "image_tags": ["Grand Prismatic Spring Yellowstone satellite photo", "volcanic caldera cross section diagram USGS", "basalt lava field geothermal landscape", "volcanic lightning ash column photography"],
        "gif_tags": ["volcano lava flow loop gif", "geyser water eruption steam animation", "magma chamber subterranean simulation gif"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "pure_white",
    },
    {
        "id": "magnetic_reversal",
        "category": "Geologia & Catástrofes",
        "icon": "🧭",
        "title": "A Inversão dos Polos Magnéticos da Terra",
        "hook": "O Polo Norte magnético está se movendo cinquenta quilômetros por ano e os cientistas alertam sobre uma inversão.",
        "script": "O campo magnético da Terra é o escudo invisível primordial que desvia ventos solares letais e protege a atmosfera da radiação cósmica do espaço profundo. No entanto, esse escudo protetor não é estático. Amostras de rochas vulcânicas no fundo do oceano Atlântico revelam que a cada duzentos a trezentos mil anos os polos magnéticos do planeta enfraquecem e invertem completamente de posição: o Polo Norte vira Polo Sul e vice-versa. Atualmente, o Polo Norte magnético está se deslocando em velocidade recorde do Ártico canadense em direção à Sibéria, enquanto o campo global perdeu quase dez por cento de intensidade no último século. Durante uma transição de inversão, a magnetosfera pode sofrer colapso temporário, expondo redes elétricas satelitais a apagões severos e intensificando a incidência de mutações biológicas na biosfera.",
        "terms": ["Earth magnetic field aurora borealis northern lights solar wind space 4k", "compass needle spinning planet earth magnetosphere 3d"],
        "video_tags": ["aurora borealis green night sky timelapse 4k", "earth magnetosphere solar storm 3d animation", "compass navigation needle brass macro", "sun solar flare coronal mass ejection"],
        "image_tags": ["aurora borealis green curtains Iceland NASA", "earth geodynamo magnetic core simulation", "paleomagnetic oceanic ridge stripe anomaly", "solar flare SDO NASA observatory"],
        "gif_tags": ["aurora borealis shimmering loop gif", "earth magnetic field lines dynamic gif", "compass spinning wildly animated gif"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "cyber_green",
    },
    {
        "id": "technological_singularity",
        "category": "Inteligência Artificial & Futuro",
        "icon": "🤖",
        "title": "A Singularidade Tecnológica: O Ponto de Não Retorno",
        "hook": "Em poucas décadas, uma inteligência artificial poderá se autoaperfeiçoar em segundos e superar toda a história humana.",
        "script": "Cientistas da computação e filósofos da tecnologia chamam de Singularidade o momento histórico em que uma inteligência artificial geral alcançará a capacidade de aprimorar o próprio código sem intervenção humana. Uma vez iniciado esse ciclo recursivo de autoevolução, cada iteração gerará uma máquina mais inteligente que a anterior em escala exponencial. O que levaria séculos de pesquisa acadêmica para cientistas biológicos poderá ser resolvido em frações de segundo por redes neurais autônomas. Esse salto civilizatório trará a cura para todas as doenças degenerativas, energia limpa infinita e exploração interplanetária, mas também colocará a espécie humana diante de um horizonte de eventos imprevisível. Quando criamos algo cognitivamente superior a nós mesmos, deixamos de ser os autores definitivos do destino deste planeta.",
        "terms": ["artificial intelligence neural network futuristic server quantum computer glowing blue 4k", "cyberpunk digital consciousness humanoid robotics data"],
        "video_tags": ["server room data center blue leds 4k", "neural network glowing connections 3d", "humanoid robot face subtle motion", "microchip processor wafer microscopic silicon"],
        "image_tags": ["NVIDIA AI supercomputer datacenter racks", "quantum computer core dilution refrigerator", "silicon chip circuit electron microscope", "artificial neural network node graph"],
        "gif_tags": ["binary matrix digital rain loop gif", "neural network glowing synapse connection gif", "robotic eye aperture focusing animation"],
        "voice": "pt-BR-ThalitaMultilingualNeural",
        "voice_rate": 1.15,
        "style": "electric_cyan",
    },
    {
        "id": "microbiome_universe",
        "category": "Biologia & Fatos Bizarros",
        "icon": "🦠",
        "title": "Você é Mais Bactéria do que Humano",
        "hook": "Cinquenta por cento do que você chama de 'você' nem sequer tem DNA humano.",
        "script": "Mais de cinquenta por cento das células que compõem o seu corpo nem sequer possuem DNA humano. No seu organismo habitam mais de trinta e oito trilhões de bactérias, fungos e microrganismos que formam o chamado microbioma. Longe de serem invasores nocivos, esses seres invisíveis produzem mais de noventa por cento da serotonina responsável pelo seu bem-estar emocional, treinam o seu sistema imunológico contra doenças graves e regulam o seu apetite. Estudos recentes revelaram que o intestino se comunica diretamente com o cérebro através do nervo vago, alterando as decisões e preferências que você toma todos os dias. Você não é um organismo isolado, mas sim um ecossistema complexo e fascinante em constante equilíbrio.",
        "terms": ["microbiology bacteria cells microscopic organism biology 4k", "dna cell division science laboratory human body"],
        "video_tags": ["microscopic bacteria moving slow motion 4k", "dna double helix rotating glow", "cellular division mitosis microscopy", "laboratory microscope lens focus scientist"],
        "image_tags": ["gut microbiome bacteria electron microscope false color", "human chromosomes karyotype DNA fluorescent", "tardigrade water bear electron micrograph", "stem cell colony petri dish culture"],
        "gif_tags": ["mitosis cell division animated gif", "dna strand spinning loop gif", "bacteria swimming flagella microscopy loop"],
        "voice": "pt-BR-FranciscaNeural",
        "voice_rate": 1.12,
        "style": "cyber_green",
    },
    {
        "id": "aladdin_blackrock",
        "category": "Finanças & Monopólios",
        "icon": "🏦",
        "title": "Aladdin: O Algoritmo de 21 Trilhões de Dólares",
        "hook": "Existe um computador em Washington que decide o destino de vinte e um trilhões de dólares todos os dias.",
        "script": "Existe um computador em Washington que decide o destino de vinte e um trilhões de dólares todos os dias. Ele se chama Aladdin, uma rede neural operada pela gestora BlackRock que analisa cada ação, título de dívida e imóvel no planeta em frações de segundo. Seis mil servidores processam relatórios de bancos centrais, variações climáticas e movimentos militares para prever crises antes que elas ocorram. Hoje, os maiores fundos de pensão, bancos privados e governos soberanos não compram nem vendem ativos sem consultar o sistema. Quando o algoritmo identifica risco em um setor, bilhões são retirados em milissegundos, provocando falências sem que uma única decisão humana tenha sido tomada. Não existe conspiração secreta em salas fechadas: o mercado global opera sob as regras matemáticas exatas de uma única máquina. E a razão pela qual ninguém consegue deter esse monopólio silencioso é porque...",
        "terms": ["dark server room data center financial trading floor monitors 4k", "algorithmic network nodes glowing blackrock wall street"],
        "video_tags": ["server room data center dark 4k", "financial trading floor monitors stock exchange", "wall street time lapse night crowd", "algorithmic network nodes glowing data"],
        "image_tags": ["BlackRock headquarters skyscraper New York", "Aladdin risk management software data center", "Wall Street stock exchange floor historical", "server rack glowing blue led technology"],
        "gif_tags": ["stock market ticker tape scrolling gif", "data center server lights blinking loop", "financial chart crash spike animation"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "viral_yellow",
    },
    {
        "id": "dutch_east_india",
        "category": "Finanças & Monopólios",
        "icon": "⚓",
        "title": "Companhia das Índias Orientais: O Maior Monopólio da História",
        "hook": "A empresa mais rica que já existiu na Terra não vendia tecnologia, mas especiarias e pólvora.",
        "script": "A empresa mais rica que já existiu na Terra não vendia tecnologia, mas especiarias e pólvora. Em 1637, a Companhia Holandesa das Índias Orientais atingiu um valor de mercado equivalente a quase oito trilhões de dólares modernos. Ela não era apenas uma empresa: tinha exército próprio com mais de quarenta mil soldados mercenários, duzentos navios de guerra blindados e autoridade jurídica para declarar guerra, enforcar desertores e cunhar sua própria moeda. Por quase dois séculos, essa corporação controlou o comércio de cravo e noz-moscada na Ásia executando concorrentes com brutalidade militar e pagando dividendos anuais de quarenta por cento aos seus acionistas em Amsterdã. O modelo que moldou as corporações globais de hoje nasceu de uma armada armada que comprava nações inteiras à força. E a prova de que esse império nunca desapareceu completamente começa no momento em que...",
        "terms": ["17th century warship storm ocean golden coins dutch guilders chest 4k", "ancient amsterdam harbor map handwriting ancient stock certificate"],
        "video_tags": ["historic warship stormy sea cannon fire 4k", "gold coins falling treasure chest macro", "amsterdam canals historical sailing ships", "antique parchment quill handwriting documents"],
        "image_tags": ["Dutch East India Company VOC flag galleon", "Amsterdam stock exchange 17th century painting", "VOC guilder silver coin archive", "spice trade historical engraving Asia"],
        "gif_tags": ["sailing ship storm waves loop gif", "gold coins chest shimmering loop", "vintage compass rotating historical map animation"],
        "voice": "pt-BR-DuarteNeural",
        "voice_rate": 1.12,
        "style": "gold_luxury",
    },
    {
        "id": "ben_franklin_effect",
        "category": "Psicologia Obscura",
        "icon": "♟️",
        "title": "O Efeito Ben Franklin: Como Fazer um Inimigo Confiar em Você",
        "hook": "Se você quer que alguém passe a gostar de você, não faça um favor a essa pessoa.",
        "script": "Se você quer que alguém passe a gostar de você, não faça um favor a essa pessoa. Peça para ela fazer um favor para você. Em 1737, Benjamin Franklin conquistou a lealdade de um rival político declarado na Pensilvânia pedindo emprestado um livro raro de sua biblioteca particular. A psicologia moderna explica isso através da dissonância cognitiva: o cérebro humano não tolera contradições entre atitudes e sentimentos. Ao gastar tempo e energia para te ajudar, a mente do adversário é forçada a justificar a própria ação, concluindo subconscientemente: se estou prestando auxílio a ele, significa que o respeito. Fazer favores coloca você na posição de devedor; pedir favores coloca você na posição de autoridade e valor. A mecânica oculta da persuasão nunca foi agradar os outros, mas fazê-los investir em você. E o gatilho exato que ativa esse comportamento sem gerar resistência é saber que...",
        "terms": ["vintage leather book turning pages close up intense eye contact chess board 4k", "two men shadow silhouettes meeting brain neural synapses firing"],
        "video_tags": ["chess game close up fingers moving king 4k", "antique library leather bound books turning", "silhouette two figures conversation low key", "clock ticking slow motion pocket watch"],
        "image_tags": ["Benjamin Franklin portrait Pennsylvania assembly", "vintage leather bound rare book library", "cognitive dissonance psychology diagram", "chess board strategic standoff black and white"],
        "gif_tags": ["chess piece moving checkmate gif", "turning pages old book timelapse loop", "neural network glowing brain thinking gif"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "viral_yellow",
    },
    {
        "id": "microexpressions_contempt",
        "category": "Psicologia Obscura",
        "icon": "👁️",
        "title": "Microexpressões de Desprezo: O Sinal de 0,04 Segundos",
        "hook": "Existe uma contração muscular facial involuntária que dura menos de um vigésimo de segundo e revela traição iminente.",
        "script": "Existe uma contração muscular facial involuntária que dura menos de um vigésimo de segundo e revela traição iminente. Pesquisadores de microexpressões identificaram que o desprezo é a única emoção humana puramente assimétrica. Enquanto a raiva e a alegria ativam os dois lados da face simultaneamente, o desprezo contrai apenas o músculo bucinador de um dos cantos da boca, levantando ligeiramente o lábio superior. Esse reflexo é controlado pelo sistema límbico e não pode ser completamente suprimido pela mente consciente, nem mesmo por mentirosos treinados. Em negociações de alto risco ou interrogatórios policiais, flagrar esse micro-movimento indica que a outra parte se considera superior e já decidiu romper o acordo antes mesmo de terminar a frase. Aprender a detectar esse detalhe muda para sempre a forma como você enxerga conversas cotidianas, porque...",
        "terms": ["macro human eye pupil dilating slow motion face portrait subtle smirk 4k", "interrogation room shadows lamp thermal heat map human face"],
        "video_tags": ["macro human eye pupil contracting 4k", "facial expression subtle smirk slow motion", "interrogation room dark shadow lighting", "biometric face scan recognition grid"],
        "image_tags": ["Paul Ekman facial action coding system chart", "human face muscle anatomy buccinator", "microexpression asymmetry high speed photography", "thermal imaging human face emotions"],
        "gif_tags": ["human eye pupil dilation macro loop gif", "facial recognition scanner grid tracking gif", "subtle smirk mouth corner twitch loop"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "danger_red",
    },
    {
        "id": "false_vacuum_decay",
        "category": "Física Extrema & Cosmos",
        "icon": "💥",
        "title": "Decaimento do Vácuo Falso: O Fim da Matéria na Velocidade da Luz",
        "hook": "O universo pode ser destruído a qualquer momento por uma bolha microscópica que viaja à velocidade da luz.",
        "script": "O universo pode ser destruído a qualquer momento por uma bolha microscópica que viaja à velocidade da luz. Cálculos do Grande Colisor de Hádrons indicam que o campo de Higgs, responsável por dar massa a todas as partículas conhecidas, pode não estar no seu nível mínimo de energia, mas sim em um estado temporário chamado vácuo falso. Se em qualquer ponto do cosmos uma flutuação quântica fizer esse campo deslizar para o verdadeiro estado fundamental, uma bolha de vácuo real começará a se expandir instantaneamente. Dentro dessa esfera, as constantes físicas fundamentais mudam: elétrons deixam de orbitar núcleos, átomos se desintegram e a química deixa de existir. Como a borda dessa bolha se move exatamente a trezentos mil quilômetros por segundo, nenhum telescópio conseguiria detectá-la antes que ela varresse nosso sistema solar. A estabilidade de toda a matéria que você toca depende do fato de que...",
        "terms": ["subatomic particle collision cern simulation expanding cosmic shockwave stars 4k", "quantum foam distortion 3d render higgs field theoretical"],
        "video_tags": ["particle accelerator collision beam 4k", "cosmic shockwave destroying stars 3d", "quantum vacuum fluctuations glowing grid", "supernova cosmic explosion deep space"],
        "image_tags": ["CERN Large Hadron Collider tunnel detector", "Higgs potential mexican hat graph physics", "quantum tunneling vacuum decay simulation", "deep space cosmic web voids galaxies"],
        "gif_tags": ["expanding spherical shockwave cosmos loop gif", "particle collision subatomic sparks gif", "quantum field fluctuation matrix animation"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "electric_cyan",
    },
    {
        "id": "black_hole_dilation",
        "category": "Física Extrema & Cosmos",
        "icon": "🕳️",
        "title": "Dilatação Temporal no Horizonte de Eventos: 1 Hora = 100 Anos",
        "hook": "Se você caísse em direção a um buraco negro supermassivo, veria toda a história futura do cosmos em poucos segundos.",
        "script": "Se você caísse em direção a um buraco negro supermassivo, veria toda a história futura do cosmos em poucos segundos. De acordo com a relatividade geral de Albert Einstein, a gravidade extrema deforma o tecido do espaço-tempo de maneira tão profunda que quanto mais próximo você chega do horizonte de eventos, mais devagar seu relógio bate em relação ao resto do universo. Para um observador assistindo de uma nave distante, sua queda pareceria desacelerar até congelar completamente na borda escura. No entanto, na sua própria perspectiva, você continuaria caindo normalmente, enquanto a luz de galáxias distantes alcançaria seus olhos acelerada: você testemunharia o nascimento e a morte de trilhões de estrelas antes que as forças de maré rompessem seus átomos. O tempo não é uma linha constante, mas uma ilusão elástica que se quebra quando...",
        "terms": ["black hole gravitational lensing interstellar style accretion disk glowing 4k", "cosmic time dilation clock spinning fast astronaut helmet reflection"],
        "video_tags": ["black hole gravitational lensing 3d render 4k", "accretion disk spinning glowing gas interstellar", "clock hands spinning wildly blur time lapse", "spacetime fabric grid bending deep well"],
        "image_tags": ["Event Horizon Telescope M87 black hole shadow", "gravitational lensing simulation Einstein ring", "supermassive black hole accretion disk rendering", "James Webb deep space gravitational arc"],
        "gif_tags": ["black hole accretion disk rotation loop gif", "clock hands accelerating time dilation gif", "light bending around singularity animation"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "electric_cyan",
    },
    {
        "id": "challenger_deep_pressure",
        "category": "Abismo Oceânico & Mistérios",
        "icon": "🌊",
        "title": "Depressão Challenger: A Pressão que Esmaga Titânio",
        "hook": "A quase onze quilômetros de profundidade na Fossa das Marianas, a água exerce a pressão de mil elefantes sobre a sua cabeça.",
        "script": "A quase onze quilômetros de profundidade na Fossa das Marianas, a água exerce a pressão de mil elefantes sobre a sua cabeça. A Depressão Challenger é o ponto mais profundo da crosta terrestre, um abismo onde a luz solar nunca penetrou e onde a pressão hidrostática ultrapassa cem megapascais. Se uma fissura microscópica se abrir no casco de um submarino a essa profundidade, a água entrará com força suficiente para vaporizar ossos humanos em vinte milissegundos. Apesar desse ambiente hostil, sondas robóticas encontraram anfípodes gigantes e peixes-caracol sem escamas sobrevivendo em escuridão total. Seus corpos produzem compostos celulares chamados piezólitos que impedem suas proteínas de colapsar sob a força do oceano. O homem já enviou doze astronautas à Lua, mas menos pessoas tocaram o fundo desse vale do que visitaram o espaço exterior. E o maior mistério dessas fossas permanece oculto porque...",
        "terms": ["deep sea submersible robotic arm searchlight hadal snailfish transparent 4k", "ocean trench abyssal zone dark blue underwater sonar map mariana"],
        "video_tags": ["deep sea submersible searchlight abyss 4k", "mariana trench robotic arm picking sample", "bioluminescent abyssal creatures swimming dark", "ocean depth pressure gauge dropping"],
        "image_tags": ["Mariana trench Challenger Deep bathymetry map", "Deepsea Challenger James Cameron submersible", "hadal snailfish Pseudoliparis swirei photograph", "ocean hydrothermal vent black smoker NOAA"],
        "gif_tags": ["deep sea submersible lights illuminating abyss gif", "transparent deep sea creature undulating loop", "sonar ping radar screen underwater animation"],
        "voice": "pt-BR-FranciscaNeural",
        "voice_rate": 1.12,
        "style": "electric_cyan",
    },
    {
        "id": "point_nemo_graveyard",
        "category": "Abismo Oceânico & Mistérios",
        "icon": "🛰️",
        "title": "Ponto Nemo: O Cemitério Espacial Mais Isolado da Terra",
        "hook": "Se você ficasse à deriva no Ponto Nemo, os seres humanos mais próximos de você estariam a quatrocentos quilômetros acima da sua cabeça.",
        "script": "Se você ficasse à deriva no Ponto Nemo, os seres humanos mais próximos de você estariam a quatrocentos quilômetros acima da sua cabeça. Localizado no Pacífico Sul, este é o polo de inacessibilidade oceânica, o ponto exato mais distante de qualquer costa rochosa ou ilha habitada em todo o globo. As correntes oceânicas aqui não carregam nutrientes suficientes para sustentar peixes ou algas, transformando quatro milhões de quilômetros quadrados de água em um deserto marinho quase desprovido de vida. Por causa desse isolamento absoluto, agências espaciais como a NASA e a Roscosmos usam essa coordenada como lixeira orbital, onde mais de duzentos e sessenta satélites e estações desativadas já foram afundados propositalmente. Em 2031, a Estação Espacial Internacional será desorbitada para encontrar seu descanso final nesta tumba líquida. E o silêncio perturbador desse abismo é interrompido apenas quando...",
        "terms": ["satellite reentering atmosphere burning ocean night vast empty pacific ocean 4k", "space debris resting ocean floor rust underwater station mir crash"],
        "video_tags": ["satellite space station burning reentering atmosphere 4k", "vast open ocean aerial calm blue water", "underwater sunken wreckage coral rust", "radar coordinate target ocean grid"],
        "image_tags": ["Point Nemo pole of inaccessibility globe map", "spacecraft cemetery satellite reentry debris", "Mir space station deorbit splashdown photo", "International Space Station ISS in orbit NASA"],
        "gif_tags": ["satellite burning atmospheric entry trail gif", "globe spinning zooming into empty pacific ocean loop", "radar screen sweeping solitary blip animation"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "pure_white",
    },
    {
        "id": "gobekli_tepe_megalith",
        "category": "Civilizações & Arqueologia",
        "icon": "🗿",
        "title": "Göbekli Tepe: O Monumento de 11.500 Anos que Reescreveu a História",
        "hook": "Tudo o que os livros escolares ensinaram sobre a origem da civilização humana foi refutado sob a areia da Turquia.",
        "script": "Tudo o que os livros escolares ensinaram sobre a origem da civilização humana foi refutado sob a areia da Turquia. Em Göbekli Tepe, arqueólogos desenterraram dezenas de pilares megalíticos em formato de T pesando até vinte toneladas cada, esculpidos com relevos tridimensionais de leões, escorpiões e pássaros. A datação por radiocarbono confirmou que a estrutura tem mais de onze mil e quinhentos anos de idade, erguida no final da última era glacial, milênios antes da invenção da cerâmica, da metalurgia ou da roda. A teoria convencional afirmava que a agricultura era um pré-requisito para que tribos nômades construíssem templos organizados; Göbekli Tepe provou o oposto: a necessidade de cultuar algo grandioso forçou os homens a se fixarem e criarem a agricultura. Mais intrigante ainda: o complexo foi intencionalmente enterrado à mão por seus próprios construtores antes de desaparecer. E o motivo desse soterramento sistemático aponta para o fato de que...",
        "terms": ["gobekli tepe stone pillar relief carving ancient archaeological excavation 4k", "prehistoric megalith sunset turkey ancient stone mason chiseling"],
        "video_tags": ["gobekli tepe aerial drone sweep sunrise 4k", "megalithic stone pillar carved reliefs macro", "archaeological excavation desert dust brush", "ancient stonehenge monoliths golden hour"],
        "image_tags": ["Gobekli Tepe T-shaped pillar lion relief Klaus Schmidt", "Sanliurfa archaeological site excavation trench", "Neolithic stone tools carving limestone", "Younger Dryas comet impact theoretical map"],
        "gif_tags": ["gobekli tepe 3d reconstruction sweep gif", "ancient stone carving animation loop", "dust wind blowing across desert megaliths gif"],
        "voice": "pt-BR-DuarteNeural",
        "voice_rate": 1.12,
        "style": "gold_luxury",
    },
    {
        "id": "bronze_age_collapse",
        "category": "Civilizações & Arqueologia",
        "icon": "⚔️",
        "title": "O Colapso da Idade do Bronze: 8 Impérios Sumiram em 50 Anos",
        "hook": "Em menos de meio século, oito das maiores civilizações do planeta foram completamente apagadas da história ao mesmo tempo.",
        "script": "Em menos de meio século, oito das maiores civilizações do planeta foram completamente apagadas da história ao mesmo tempo. Por volta de 1177 antes de Cristo, o Mediterrâneo operava uma rede comercial próspera e interconectada entre Egito, Micenas, Creta, Babilônia e o Império Hitita. Em poucas décadas, quase todas as capitais fortificadas foram queimadas até o chão, sistemas de escrita desapareceram e a humanidade afundou em uma era das trevas que durou quatrocentos anos. Documentos sobreviventes gravados em argila mencionam a chegada repentina de invasores misteriosos apelidados de Povos do Mar, mas análises de anéis de árvores e sedimentos mostram que uma seca severa de um século provocou fomes em massa e rebeliões em cadeia. A primeira sociedade globalizada ruiu como um castelo de cartas quando sua cadeia de suprimentos foi interrompida. E o alerta que esse colapso antigo deixa para o mundo contemporâneo é que...",
        "terms": ["ancient city burning bronze age ruins night mycenaean palace destroyed 4k", "clay cuneiform tablet macro burning ancient warriors longboats"],
        "video_tags": ["ancient temple columns burning flames night 4k", "clay tablet cuneiform inscription macro", "archaeological ruins crumbling stone wall", "ancient war fleet sailing dark stormy coast"],
        "image_tags": ["Hattusa Hittite capital burned ruins Anatolia", "Medinet Habu relief Sea Peoples battle Ramesses III", "Mycenae Lion Gate archaeological site Greece", "cuneiform tablet letter pleading for grain famine"],
        "gif_tags": ["ancient city fire burning smoke loop gif", "ancient galley ship rowing ocean animation", "parchment crumbling burn edge transition gif"],
        "voice": "pt-BR-AntonioNeural",
        "voice_rate": 1.15,
        "style": "danger_red",
    },
]

VOICE_CATALOG = [
    {
        "id": "pt-BR-AntonioNeural",
        "name": "Antônio (pt-BR)",
        "gender": "Masculino",
        "tone": "Voz grave e sóbria, ideal para documentários e narrativas científicas.",
        "badge": "Documentário / Ciência",
        "sample_text": "No coração da galáxia, a gravidade distorce as leis fundamentais do espaço e do tempo.",
        "preview_url": "/audio/voices/pt-BR-AntonioNeural.mp3",
    },
    {
        "id": "pt-BR-FranciscaNeural",
        "name": "Francisca (pt-BR)",
        "gender": "Feminino",
        "tone": "Voz articulada e envolvente, ideal para comunicação e divulgação.",
        "badge": "Educacional / Narrativa",
        "sample_text": "Você já parou para pensar no que realmente acontece dentro do cérebro humano?",
        "preview_url": "/audio/voices/pt-BR-FranciscaNeural.mp3",
    },
    {
        "id": "pt-BR-ThalitaMultilingualNeural",
        "name": "Thalita (pt-BR)",
        "gender": "Feminino",
        "tone": "Voz contemporânea, cadência ágil e dicção precisa.",
        "badge": "Dinâmico / Moderno",
        "sample_text": "Três fatos inacreditáveis que vão mudar o jeito como você enxerga a realidade.",
        "preview_url": "/audio/voices/pt-BR-ThalitaMultilingualNeural.mp3",
    },
    {
        "id": "pt-PT-DuarteNeural",
        "name": "Duarte (pt-PT)",
        "gender": "Masculino",
        "tone": "Voz formal e pausada, perfeita para história e grandes explorações.",
        "badge": "Histórico / Clássico",
        "sample_text": "No vasto cosmos da ciência, cada detalhe conta uma história sobre o universo.",
        "preview_url": "/audio/voices/pt-PT-DuarteNeural.mp3",
    },
    {
        "id": "pt-PT-RaquelNeural",
        "name": "Raquel (pt-PT)",
        "gender": "Feminino",
        "tone": "Dicção clara e expressiva, excelente para ciências e natureza.",
        "badge": "Natureza / Ciência",
        "sample_text": "As descobertas mais fascinantes da natureza continuam a desafiar a nossa compreensão.",
        "preview_url": "/audio/voices/pt-PT-RaquelNeural.mp3",
    },
]

SUBTITLE_STYLES = [
    {
        "id": "viral_yellow",
        "name": "Amarelo Editorial",
        "font_name": "BeVietnamPro-Bold.ttf",
        "text_fore_color": "#FFE600",
        "stroke_color": "#000000",
        "stroke_width": 2.5,
        "subtitle_display_mode": "word_by_word",
        "subtitle_animation": "pop_spring",
        "subtitle_position": "bottom",
        "font_size": 70,
        "description": "Amarelo de alta legibilidade com contorno escuro e destaque sincronizado.",
    },
    {
        "id": "pure_white",
        "name": "Branco Minimalista",
        "font_name": "BeVietnamPro-Bold.ttf",
        "text_fore_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 2.0,
        "subtitle_display_mode": "sentence",
        "subtitle_animation": "none",
        "subtitle_position": "bottom",
        "font_size": 65,
        "description": "Tipografia branca limpa e discreta, sem animações invasivas.",
    },
    {
        "id": "electric_cyan",
        "name": "Ciano Técnico",
        "font_name": "BeVietnamPro-Bold.ttf",
        "text_fore_color": "#00F0FF",
        "stroke_color": "#000000",
        "stroke_width": 2.5,
        "subtitle_display_mode": "word_by_word",
        "subtitle_animation": "pop_spring",
        "subtitle_position": "bottom",
        "font_size": 70,
        "description": "Tom ciano sóbrio com ótimo contraste para tecnologia e cosmos.",
    },
    {
        "id": "cyber_green",
        "name": "Verde Neutro",
        "font_name": "BeVietnamPro-Bold.ttf",
        "text_fore_color": "#10B981",
        "stroke_color": "#000000",
        "stroke_width": 2.2,
        "subtitle_display_mode": "word_by_word",
        "subtitle_animation": "pop_spring",
        "subtitle_position": "bottom",
        "font_size": 68,
        "description": "Verde esmeralda equilibrado para ciências naturais e biologia.",
    },
    {
        "id": "hormozi_bold",
        "name": "Hormozi Viral (Destaque Máximo)",
        "font_name": "BeVietnamPro-Bold.ttf",
        "text_fore_color": "#FFE600",
        "stroke_color": "#000000",
        "stroke_width": 3.0,
        "text_background_color": "#000000",
        "rounded_subtitle_background": True,
        "subtitle_display_mode": "word_by_word",
        "subtitle_animation": "pop_spring",
        "subtitle_position": "bottom",
        "font_size": 76,
        "description": "Amarelo ouro sobre fundo escuro arredondado com alta retenção para Shorts/TikTok.",
    },
    {
        "id": "dark_box",
        "name": "Faixa Documentário BBC",
        "font_name": "BeVietnamPro-Bold.ttf",
        "text_fore_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 1.5,
        "text_background_color": "#111827",
        "rounded_subtitle_background": True,
        "subtitle_display_mode": "sentence",
        "subtitle_animation": "none",
        "subtitle_position": "bottom",
        "font_size": 65,
        "description": "Branco cristalino sobre fundo escuro elegante estilo documentário BBC.",
    },
]


class UpdateConfigRequest(BaseModel):
    llm_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    pexels_api_keys: Optional[str] = None
    pixabay_api_keys: Optional[str] = None
    upload_post_enabled: Optional[bool] = None
    upload_post_api_key: Optional[str] = None
    upload_post_username: Optional[str] = None
    upload_post_platforms: Optional[List[str]] = None
    upload_post_auto_upload: Optional[bool] = None
    upload_post_youtube_privacy_status: Optional[str] = None
    upload_post_youtube_made_for_kids: Optional[bool] = None


@router.get("/saas/presets", summary="Obter templates e configurações de canais dark de ciência")
def get_saas_presets(request: Request):
    """Retorna templates de roteiro de ciência, catálogo de vozes e estilos virais."""
    return utils.get_response(
        200,
        {
            "science_presets": SCIENCE_PRESETS,
            "voices": VOICE_CATALOG,
            "subtitle_styles": SUBTITLE_STYLES,
            "fonts": ["BeVietnamPro-Bold.ttf", "STHeitiMedium.ttc"],
        },
    )


@router.get("/saas/status", summary="Verificar saúde e configurações do sistema")
def get_saas_status(request: Request):
    """Informa o status do FFmpeg, provedor LLM ativo e estatísticas de tarefas."""
    ffmpeg_bin = utils.get_ffmpeg_binary()
    all_tasks, total_tasks = sm.state.get_all_tasks(page=1, page_size=5)

    current_provider = config.app.get("llm_provider", "gemini")
    has_gemini = bool(config.app.get("gemini_api_key", ""))
    has_openai = bool(config.app.get("openai_api_key", ""))
    has_deepseek = bool(config.app.get("deepseek_api_key", ""))
    pexels_keys = config.app.get("pexels_api_keys", [])
    has_pexels = bool(pexels_keys)
    pixabay_keys = config.app.get("pixabay_api_keys", [])
    has_pixabay = bool(pixabay_keys)

    from app.services import upload_post
    up_platforms = config.app.get("upload_post_platforms", ["tiktok", "youtube"])
    if isinstance(up_platforms, str):
        up_platforms = [p.strip() for p in up_platforms.split(",") if p.strip()]

    upload_post_info = {
        "enabled": bool(config.app.get("upload_post_enabled", False)),
        "configured": upload_post.upload_post_service.is_configured(),
        "username": config.app.get("upload_post_username", ""),
        "has_api_key": bool(config.app.get("upload_post_api_key", "")),
        "platforms": up_platforms,
        "auto_upload": bool(config.app.get("upload_post_auto_upload", False)),
        "youtube_privacy_status": config.app.get("upload_post_youtube_privacy_status", "public"),
        "youtube_made_for_kids": bool(config.app.get("upload_post_youtube_made_for_kids", False)),
    }

    return utils.get_response(
        200,
        {
            "status": "online",
            "app_name": "PrintMoney Studio",
            "ffmpeg_ready": bool(ffmpeg_bin),
            "ffmpeg_path": ffmpeg_bin,
            "llm_provider": current_provider,
            "providers_configured": {
                "gemini": has_gemini,
                "openai": has_openai,
                "deepseek": has_deepseek,
                "pexels": has_pexels,
                "pixabay": has_pixabay,
            },
            "has_pexels": has_pexels,
            "has_pixabay": has_pixabay,
            "upload_post": upload_post_info,
            "total_tasks_created": total_tasks,
            "recent_tasks": all_tasks[:5],
        },
    )


MEDIA_TAGS_COLLECTION = {
    "astrophysics": {
        "title": "Astrofísica & Espaço Profundo",
        "video_tags": [
            "black hole accretion disk 4k",
            "galaxy cluster stars deep space",
            "nebula cosmic stellar nursery",
            "space telescope orbit earth",
            "solar flare coronal mass ejection",
            "pulsar neutron star magnetic simulation",
        ],
        "image_tags": [
            "James Webb cosmic cliffs Carina",
            "Hubble ultra deep field galaxies",
            "supermassive black hole event horizon",
            "Andromeda galaxy high resolution M31",
            "Saturn rings Cassini spacecraft NASA",
            "Milky Way galactic center infrared",
        ],
        "gif_tags": [
            "pulsar rotating radiation beam gif",
            "solar system orbits simulation animation",
            "black hole gravitational lensing loop",
            "supernova shockwave explosion animation",
            "spiral galaxy rotation loop",
        ],
    },
    "marine_abyss": {
        "title": "Abismo Oceânico & Criaturas",
        "video_tags": [
            "deep ocean trench dark underwater",
            "submersible ROV exploration abyss",
            "bioluminescent siphonophore jellyfish",
            "hydrothermal vent black smoker deep sea",
            "Mariana Trench Challenger Deep",
        ],
        "image_tags": [
            "deep sea anglerfish bioluminescence NOAA",
            "bathyscaphe Trieste exploration trench",
            "ocean floor tectonic rift benthic",
            "giant squid specimen deep ocean",
            "abyssal plains sediment exploration",
        ],
        "gif_tags": [
            "bioluminescent jellyfish pulsing loop gif",
            "submarine descent dark ocean animation",
            "sonar radar pulse ocean wave gif",
            "iceberg calving underwater loop",
        ],
    },
    "neuroscience": {
        "title": "Neurociência & Cérebro",
        "video_tags": [
            "neurons firing electrical synapse 4k",
            "macro human iris pupil dilation",
            "fMRI brain scan medical laboratory",
            "consciousness neural pathways glowing",
        ],
        "image_tags": [
            "synapse electron microscope neural network",
            "human brain anatomy cross section cortex",
            "retina rods and cones microscopic",
            "EEG brain wave electrical mapping",
        ],
        "gif_tags": [
            "action potential neural impulse firing gif",
            "human eye pupil iris dilation loop",
            "brain wave EEG oscillation animation",
            "optical illusion spinning spiral loop",
        ],
    },
    "quantum_physics": {
        "title": "Física Quântica & Multiverso",
        "video_tags": [
            "quantum processor dilution refrigerator 4k",
            "laser optics beam dark laboratory",
            "particle accelerator collider tunnel",
            "wave interference ripples water slow motion",
        ],
        "image_tags": [
            "CERN Large Hadron Collider ATLAS detector",
            "IBM quantum computer chandelier cryostat",
            "double slit experiment fringes diagram",
            "quantum entanglement photon laser table",
        ],
        "gif_tags": [
            "double slit wave interference pattern gif",
            "quantum qubit superposition bloch sphere loop",
            "spacetime curvature gravity grid animation",
            "laser diffraction pattern animated gif",
        ],
    },
    "archaeology": {
        "title": "Arqueologia & Civilizações Antigas",
        "video_tags": [
            "ancient Greek temple columns ruins aerial",
            "underwater archaeology diver sunken statue",
            "Egyptian pyramids Giza desert cinematic",
            "antique watch gears clockwork macro",
        ],
        "image_tags": [
            "Antikythera mechanism bronze gear artifact",
            "sunken city Heracleion granite pharaoh",
            "Rosetta stone British museum inscriptions",
            "ancient Roman mosaic Pompeii high resolution",
        ],
        "gif_tags": [
            "Antikythera mechanism 3d gear simulation gif",
            "ancient astrolabe astronomical calculation loop",
            "gear train mechanical movement loop gif",
        ],
    },
    "economy_markets": {
        "title": "Economia, Dinheiro & Mercados",
        "video_tags": [
            "banknotes currency printing press rolling 4k",
            "gold bars vault shiny stacked bullion",
            "stock exchange trading floor screens",
            "digital financial candlestick chart dark",
        ],
        "image_tags": [
            "Federal Reserve vault steel security door",
            "Weimar hyperinflation historical archive",
            "Semper Augustus tulip painting 1637",
            "London gold vault bullion depository",
        ],
        "gif_tags": [
            "candlestick stock chart ticking animation",
            "banknote printing press cylinder loop gif",
            "gold coin spinning loop",
        ],
    },
    "extreme_earth": {
        "title": "Geologia Extrema & Vulcanismo",
        "video_tags": [
            "volcano eruption lava fountain slow motion",
            "geothermal geyser steam eruption Yellowstone",
            "aurora borealis green ribbons night sky",
            "volcanic ash lightning thunderstorm",
        ],
        "image_tags": [
            "Grand Prismatic Spring Yellowstone aerial",
            "geodynamo magnetic field earth core USGS",
            "basalt lava column landscape Iceland",
            "solar flare SDO observatory NASA",
        ],
        "gif_tags": [
            "volcanic lava flow continuous loop gif",
            "earth magnetic field lines dynamic gif",
            "geyser eruption boiling steam animation",
        ],
    },
    "ai_future": {
        "title": "Inteligência Artificial & Fronteiras",
        "video_tags": [
            "datacenter server racks blue glowing leds",
            "humanoid robot face subtle expressions",
            "silicon microchip wafer electron microscope",
            "neural network node connections 3d",
        ],
        "image_tags": [
            "NVIDIA AI supercomputer datacenter clusters",
            "quantum chip processor optical table",
            "integrated circuit transistor microscopic SEM",
            "fiber optic network undersea cable map",
        ],
        "gif_tags": [
            "neural network synapse learning animation",
            "binary matrix code stream continuous loop",
            "robotic iris camera shutter focus gif",
        ],
    },
}


@router.get("/saas/tags", summary="Banco expandido de tags e categorias para vídeos, imagens e GIFs")
def get_media_tags(request: Request):
    """Retorna clusters de tags especializadas para busca de vídeos, imagens e GIFs de domínio público."""
    return utils.get_response(200, {"tag_categories": MEDIA_TAGS_COLLECTION})


@router.get("/saas/materials", summary="Listar acervo de mídias locais (vídeos, imagens e GIFs)")
def get_local_materials(request: Request):
    """Retorna arquivos de mídia presentes em storage/local_videos com metadados e classificação."""
    import os
    local_dir = utils.storage_dir("local_videos")
    files = []
    if os.path.exists(local_dir):
        for fname in os.listdir(local_dir):
            lower = fname.lower()
            if lower.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm", ".jpg", ".jpeg", ".png", ".webp", ".gif")):
                fpath = os.path.join(local_dir, fname)
                try:
                    fsize = os.path.getsize(fpath)
                    media_type = "gif" if lower.endswith(".gif") else ("image" if lower.endswith((".jpg", ".jpeg", ".png", ".webp")) else "video")
                    files.append({
                        "name": fname,
                        "size_bytes": fsize,
                        "size_mb": round(fsize / (1024 * 1024), 2),
                        "type": media_type,
                    })
                except Exception:
                    pass
    files.sort(key=lambda x: x["name"])
    return utils.get_response(200, {"materials": files, "count": len(files)})


@router.post("/saas/upload_material", summary="Enviar novo clipe para o acervo local")
async def upload_local_material(file: UploadFile = File(...)):
    """Recebe um arquivo de vídeo e armazena em storage/local_videos."""
    import os
    import shutil
    local_dir = utils.storage_dir("local_videos")
    os.makedirs(local_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in file.filename)
    dest_path = os.path.join(local_dir, safe_name)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return utils.get_response(200, {"success": True, "filename": safe_name, "message": "Arquivo adicionado ao acervo com sucesso"})


@router.delete("/saas/materials/{filename}", summary="Excluir vídeo do acervo local")
def delete_local_material(filename: str, request: Request):
    """Remove um clipe específico do diretório storage/local_videos."""
    import os
    local_dir = utils.storage_dir("local_videos")
    safe_name = os.path.basename(filename)
    target = os.path.join(local_dir, safe_name)
    if os.path.exists(target) and os.path.isfile(target):
        try:
            os.remove(target)
            return utils.get_response(200, {"success": True, "message": f"{safe_name} removido com sucesso"})
        except Exception as e:
            return utils.get_response(500, message=f"Erro ao excluir arquivo: {str(e)}")
    return utils.get_response(404, message="Arquivo não encontrado no acervo local")


@router.get("/saas/bgms", summary="Listar trilhas sonoras disponíveis")
def get_saas_bgms(request: Request):
    """Retorna lista de trilhas musicais disponíveis em resource/songs com preview."""
    import os
    from app.services import bgm as bgm_service
    songs = []
    labels = {
        "output000.mp3": "🌌 Ambiente Espacial & Infinito",
        "output001.mp3": "🔬 Documentário Científico & Foco",
        "output002.mp3": "🌑 Tensão & Mistério Cósmico",
        "output003.mp3": "🌊 Profundezas & Ondas Submarinas",
        "output004.mp3": "💼 Corporativo & Inovação Moderna",
        "output005.mp3": "⏳ Reflexão Filosófica & Tempo",
        "output006.mp3": "🤖 Batida Minimalista & Tech",
        "output007.mp3": "⚔️ Cinemático Épico & Triunfo",
        "output008.mp3": "🏛️ Arqueologia & Civilizações Perdidas",
        "output009.mp3": "🧠 Neurociência & Suspense Psicológico",
        "output010.mp3": "🚀 Viagem Interestelar & Propulsão",
        "output011.mp3": "🌋 Natureza Selvagem & Vulcanismo",
        "output012.mp3": "📈 Economia Global & Wall Street",
        "output013.mp3": "🕵️ Investigação Dark & Segredos",
        "output014.mp3": "✨ Inspiração & Superação Humana",
        "output015.mp3": "🛸 Teoria Alienígena & Enigma",
        "output016.mp3": "🧊 Geleiras & Abismo Polar",
        "output017.mp3": "💻 Cyberpunk & Inteligência Artificial",
        "output018.mp3": "🎻 Drama Histórico & Cordas",
        "output019.mp3": "🔭 Descoberta Astronômica & Esperança",
        "output020.mp3": "🔥 Ação Dinâmica & Pulso Forte",
        "output021.mp3": "🍃 Tranquilidade Zen & Paisagem",
        "output022.mp3": "🌪️ Catástrofes Naturais & Tensão",
        "output023.mp3": "👑 Impérios Antigos & Realeza",
        "output024.mp3": "🎹 Piano Melancólico & Memória",
        "output025.mp3": "⚡ Energia Quântica & Aceleração",
        "output027.mp3": "🛡️ Conquista Épica & Glória",
        "output028.mp3": "🛰️ Satélites Orbitais & Silêncio",
        "output029.mp3": "🎵 Encerramento Suave & Fade",
    }
    for file_path in bgm_service.list_bgm_files():
        fname = os.path.basename(file_path)
        label = labels.get(fname, f"Trilha Sonora ({fname})")
        songs.append({
            "name": label,
            "filename": fname,
            "preview_url": f"/songs/{fname}",
        })
    return utils.get_response(200, {"songs": songs})


@router.get("/saas/bgm/incompetech", summary="Catálogo de BGM Royalty-Free Incompetech")
def get_incompetech_bgm(
    request: Request,
    feel: Optional[str] = Query(None, description="Filtrar por emoção / mood"),
    genre: Optional[str] = Query(None, description="Filtrar por gênero musical"),
    min_bpm: Optional[float] = Query(None, description="BPM mínimo"),
    max_bpm: Optional[float] = Query(None, description="BPM máximo"),
    q: Optional[str] = Query(None, description="Busca textual por título ou termo"),
    limit: int = Query(25, ge=1, le=100, description="Limite de faixas retornadas"),
):
    """Retorna lista de faixas musicais do acervo Incompetech (Kevin MacLeod) com suporte a filtros."""
    from app.services import incompetech_bgm

    tracks = incompetech_bgm.search_incompetech_tracks(
        feel=feel,
        genre=genre,
        min_bpm=min_bpm,
        max_bpm=max_bpm,
        query=q,
        limit=limit,
    )
    return utils.get_response(200, tracks)


@router.post("/saas/config", summary="Atualizar chaves e provedor LLM")
def update_saas_config(request: Request, body: UpdateConfigRequest):
    """Atualiza as chaves da API e salva diretamente no config.toml."""
    from app.config.config import save_config

    updated = False
    if body.llm_provider:
        config.app["llm_provider"] = body.llm_provider
        updated = True
    if body.gemini_api_key is not None:
        config.app["gemini_api_key"] = body.gemini_api_key
        updated = True
    if body.openai_api_key is not None:
        config.app["openai_api_key"] = body.openai_api_key
        updated = True
    if body.deepseek_api_key is not None:
        config.app["deepseek_api_key"] = body.deepseek_api_key
        updated = True
    if body.pexels_api_keys is not None:
        config.app["pexels_api_keys"] = [k.strip() for k in body.pexels_api_keys.split(",") if k.strip()]
        updated = True
    if body.pixabay_api_keys is not None:
        config.app["pixabay_api_keys"] = [k.strip() for k in body.pixabay_api_keys.split(",") if k.strip()]
        updated = True
    if body.upload_post_enabled is not None:
        config.app["upload_post_enabled"] = bool(body.upload_post_enabled)
        updated = True
    if body.upload_post_api_key is not None:
        config.app["upload_post_api_key"] = body.upload_post_api_key.strip()
        updated = True
    if body.upload_post_username is not None:
        config.app["upload_post_username"] = body.upload_post_username.strip()
        updated = True
    if body.upload_post_platforms is not None:
        config.app["upload_post_platforms"] = body.upload_post_platforms
        updated = True
    if body.upload_post_auto_upload is not None:
        config.app["upload_post_auto_upload"] = bool(body.upload_post_auto_upload)
        updated = True
    if body.upload_post_youtube_privacy_status is not None:
        config.app["upload_post_youtube_privacy_status"] = body.upload_post_youtube_privacy_status.strip().lower()
        updated = True
    if body.upload_post_youtube_made_for_kids is not None:
        config.app["upload_post_youtube_made_for_kids"] = bool(body.upload_post_youtube_made_for_kids)
        updated = True

    if updated:
        save_config()

    return utils.get_response(200, {"success": True, "message": "Configurações salvas com sucesso"})


class MetadataRequest(BaseModel):
    video_subject: str = ""
    video_script: str = ""
    subject: Optional[str] = None
    script: Optional[str] = None
    lead_magnet: Optional[str] = None
    affiliate_category: Optional[str] = None
    bgm_track: Optional[str] = None
    attribution: Optional[str] = None


def generate_viral_metadata(
    subject: str,
    script: str = "",
    lead_magnet: str = "",
    affiliate_category: str = "",
    bgm_track: str = "",
    attribution: str = "",
) -> dict:
    """
    Gera titulos magneticos de alto CTR, descricao otimizada para algoritmos de retencao,
    hashtags de nicho e kit de monetizacao completo (gatilho ManyChat, ponte longform, avisos CONAR/FTC),
    com suporte a atribuicao CC-BY de trilha sonora Incompetech.
    """
    from app.services.monetization_funnel import generate_monetization_pack

    if not attribution and bgm_track:
        from app.services import incompetech_bgm
        attribution = incompetech_bgm.get_cc_attribution(bgm_track)

    subj = (subject or "Fatos Extraordinarios da Ciencia").strip()
    s_clean = subj.replace("?", "").replace("!", "").strip()

    titles = [
        f"O que a Ciencia Escondeu Sobre {s_clean}...",
        f"Voce Sabia Disso Sobre {s_clean}? 😱",
        f"A Verdade Chocante Sobre {s_clean} que Quase Ninguem Conhece",
    ]

    monetization = generate_monetization_pack(
        subject=subj,
        script=script,
        lead_magnet=lead_magnet,
        affiliate_category=affiliate_category,
    )

    desc_hook = (script[:140] + "...") if script else f"Descubra os misterios e revelacoes fascinantes sobre {s_clean}."
    conar_disclosure = monetization.get("affiliate_disclosures", {}).get("conar_br", "")
    description = (
        f"{desc_hook}\n\n"
        f"👉 Inscreva-se para mais curiosidades cientificas e documentarios diarios!\n"
        f"💬 O que voce achou dessa descoberta? Comente abaixo!\n\n"
        f"⚖️ {conar_disclosure}"
    )
    if attribution:
        description = f"{description}\n\n🎵 Trilha Sonora:\n{attribution}"

    base_tags = [
        "#curiosidades", "#ciencia", "#fatoscuriosos", "#misterios",
        "#vocesabia", "#aprender", "#educacao", "#shorts", "#tiktokviral",
        "#reels", "#fatosdesconhecidos", "#astronomia", "#natureza", "#historia"
    ]
    specific_tags = []
    for word in s_clean.lower().split():
        if len(word) > 4 and word.isalnum():
            specific_tags.append(f"#{word}")
    all_hashtags = (specific_tags[:4] + base_tags)[:16]
    hashtags_str = " ".join(all_hashtags)

    full_clipboard_text = (
        f"📌 TITULO:\n{titles[0]}\n\n"
        f"📝 DESCRICAO:\n{description}\n\n"
        f"💬 COMENTARIO FIXADO (GATILHO DE DM & PONTE):\n{monetization['pinned_comment_dm_trigger']}\n\n"
        f"🏷️ HASHTAGS:\n{hashtags_str}\n\n"
        f"⚖️ DIVULGACAO DE AFILIADOS:\n{conar_disclosure}"
    )

    result = {
        "titles": titles,
        "description": description,
        "hashtags": all_hashtags,
        "hashtags_text": hashtags_str,
        "clipboard_text": full_clipboard_text,
        "monetization": monetization,
        "pinned_comment": monetization["pinned_comment_dm_trigger"],
        "pinned_comment_dm_trigger": monetization["pinned_comment_dm_trigger"],
        "pinned_comment_longform_bridge": monetization["pinned_comment_longform_bridge"],
        "affiliate_disclosures": monetization["affiliate_disclosures"],
        "lead_magnet_callouts": monetization["lead_magnet_callouts"],
        "estimated_earnings": monetization["estimated_earnings"],
        "revenue_estimator": monetization["revenue_estimator"],
    }
    if attribution:
        result["attribution"] = attribution

    return result


@router.post("/saas/metadata", summary="Gerar Titulos, Descricao e Hashtags Virais")
def get_viral_metadata(body: MetadataRequest, request: Request):
    """Retorna metadados prontos para postagem no TikTok e YouTube."""
    subj = (body.video_subject or body.subject or "").strip()
    scr = (body.video_script or body.script or "").strip()
    lm = (body.lead_magnet or "").strip()
    cat = (body.affiliate_category or "").strip()
    bgm = (body.bgm_track or "").strip()
    attr = (body.attribution or "").strip()
    data = generate_viral_metadata(
        subject=subj,
        script=scr,
        lead_magnet=lm,
        affiliate_category=cat,
        bgm_track=bgm,
        attribution=attr,
    )
    return utils.get_response(200, data)


class MonetizationRequest(BaseModel):
    subject: str = Field(default="", description="Tema ou assunto do vídeo")
    script: str = Field(default="", description="Roteiro narrativo do vídeo")
    lead_magnet: str = Field(default="", description="Material gratuito ou isca digital para captura de leads")
    affiliate_category: str = Field(default="", description="Categoria de produtos afiliados recomendados")
    lead_magnet_topic: Optional[str] = Field(default=None, description="Alias para lead_magnet")
    video_subject: Optional[str] = Field(default=None, description="Alias para subject")
    video_script: Optional[str] = Field(default=None, description="Alias para script")


@router.post("/saas/monetization/funnel", summary="Gerar Funil de Monetização & Comentários Fixados")
def get_monetization_funnel(body: MonetizationRequest, request: Request):
    """Gera kit de monetização com gatilho ManyChat para direct, ponte para vídeo longo, avisos legais e projeções de RPM."""
    from app.services.monetization_funnel import generate_monetization_pack

    sub = (body.subject or body.video_subject or "").strip()
    scr = (body.script or body.video_script or "").strip()
    lm = (body.lead_magnet or body.lead_magnet_topic or "").strip()
    cat = (body.affiliate_category or "").strip()

    pack = generate_monetization_pack(
        subject=sub,
        script=scr,
        lead_magnet=lm,
        affiliate_category=cat,
    )
    return utils.get_response(200, pack)


@router.get("/saas/tasks/{task_id}/metadata", summary="Obter metadados de uma tarefa concluida")
def get_task_metadata(task_id: str, request: Request):
    """Le os metadados gerados para o video da tarefa."""
    import json
    import os
    task_dir = utils.task_dir(task_id)
    meta_file = os.path.join(task_dir, "metadata-1.json")
    if os.path.exists(meta_file):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                return utils.get_response(200, json.load(f))
        except Exception:
            pass

    task = sm.state.get_task(task_id)
    subject = ""
    script = ""
    bgm_track = ""
    if task and task.params:
        subject = getattr(task.params, "video_subject", "")
        script = getattr(task.params, "video_script", "")
        bgm_track = getattr(task.params, "bgm_name", "") or getattr(task.params, "bgm_file", "")
    return utils.get_response(200, generate_viral_metadata(subject=subject, script=script, bgm_track=bgm_track))


class AnalyzeScriptRequest(BaseModel):
    script: str = Field(default="", description="Texto do roteiro narrativo a ser analisado")
    subject: Optional[str] = Field(default="", description="Tema ou pauta do vídeo para geração de ganchos")
    video_script: Optional[str] = Field(default=None, description="Alias para compatibilidade com video_script")
    video_subject: Optional[str] = Field(default=None, description="Alias para compatibilidade com video_subject")


@router.post("/saas/script/analyze", summary="Analisar retenção viral do roteiro e ganchos A/B")
def analyze_script(body: AnalyzeScriptRequest, request: Request):
    """Analisa o roteiro para estimar retenção, pontuação de gancho e ritmo, e gera variações A/B."""
    from app.services import viral_analytics

    script_text = (body.script or body.video_script or "").strip()
    subj = (body.subject or body.video_subject or "").strip()

    analysis = viral_analytics.analyze_script_virality(script=script_text, subject=subj)
    return utils.get_response(200, analysis)


class PublishSocialRequest(BaseModel):
    task_id: Optional[str] = None
    video_path: Optional[str] = None
    title: Optional[str] = None
    platforms: Optional[List[str]] = None
    youtube_privacy_status: Optional[str] = None


@router.post("/saas/publish", summary="Publicar vídeo no TikTok e YouTube")
def publish_to_social(body: PublishSocialRequest, request: Request):
    """Envia o vídeo para o TikTok e YouTube Shorts via Upload-Post."""
    import os
    from loguru import logger
    from app.services import upload_post

    if not upload_post.upload_post_service.is_configured():
        return utils.get_response(
            400,
            message="Automação social não configurada. Defina a chave e nome de usuário do Upload-Post nas Configurações.",
        )

    target_path = None
    video_subject = body.title or "Vídeo Curto"
    video_script = ""
    task_bgm = ""

    if body.task_id:
        task = sm.state.get_task(body.task_id)
        if not task:
            return utils.get_response(404, message=f"Tarefa {body.task_id} não encontrada.")
        if not task.videos:
            return utils.get_response(400, message=f"A tarefa {body.task_id} não possui vídeos concluídos.")

        rel_or_abs = task.videos[0]
        if os.path.isabs(rel_or_abs) and os.path.exists(rel_or_abs):
            target_path = rel_or_abs
        else:
            task_dir = utils.task_dir(body.task_id)
            fname = os.path.basename(rel_or_abs)
            candidate = os.path.join(task_dir, fname)
            if os.path.exists(candidate):
                target_path = candidate
            elif os.path.exists(rel_or_abs):
                target_path = rel_or_abs

        if task.params:
            video_subject = getattr(task.params, "video_subject", "") or video_subject
            video_script = getattr(task.params, "video_script", "") or video_script
            task_bgm = getattr(task.params, "bgm_name", "") or getattr(task.params, "bgm_file", "")
    elif body.video_path:
        target_path = body.video_path

    if not target_path or not os.path.exists(target_path):
        return utils.get_response(404, message="Arquivo de vídeo não encontrado no servidor.")

    platforms = body.platforms or config.app.get("upload_post_platforms", ["tiktok", "youtube"])
    if isinstance(platforms, str):
        platforms = [p.strip() for p in platforms.split(",") if p.strip()]

    meta = generate_viral_metadata(subject=video_subject, script=video_script, bgm_track=task_bgm)
    post_title = (body.title or meta["titles"][0] or video_subject)

    youtube_extra = None
    if any(p.startswith("youtube") for p in platforms):
        yt_privacy = body.youtube_privacy_status or config.app.get("upload_post_youtube_privacy_status", "public")
        made_for_kids = bool(config.app.get("upload_post_youtube_made_for_kids", False))
        youtube_extra = {
            "youtube_title": post_title[:100],
            "youtube_description": f"{meta['description']}\n\n{meta['hashtags_text']}",
            "tags": [tag.replace("#", "") for tag in meta["hashtags"][:10]],
            "privacyStatus": yt_privacy,
            "selfDeclaredMadeForKids": made_for_kids,
            "containsSyntheticMedia": True,
        }

    try:
        logger.info(f"Publicando vídeo {target_path} para {platforms}...")
        result = upload_post.cross_post_video(
            video_path=target_path,
            title=post_title,
            platforms=platforms,
            youtube_extra=youtube_extra,
        )
        if body.task_id:
            sm.state.update_task(
                body.task_id,
                cross_post_state="complete" if result.get("success") else "failed",
                cross_post_results=[result],
                cross_post_error=result.get("error") if not result.get("success") else None,
            )
        return utils.get_response(200, result)
    except Exception as e:
        logger.exception("Falha na publicação social")
        return utils.get_response(500, message=f"Erro ao publicar: {str(e)}")


@router.get("/saas/publish/status/{request_id}", summary="Consultar status de publicação")
def get_publish_status(request_id: str, request: Request):
    """Consulta o status em tempo real de uma requisição do Upload-Post."""
    from app.services import upload_post
    status_result = upload_post.upload_post_service.check_status(request_id)
    return utils.get_response(200, status_result)


@router.get("/saas/tasks/{task_id}/publish_status", summary="Consultar status de postagem da tarefa")
def get_task_publish_status(task_id: str, request: Request):
    """Retorna o estado da postagem social automática ou manual da tarefa."""
    task = sm.state.get_task(task_id)
    if not task:
        return utils.get_response(404, message="Tarefa não encontrada")
    return utils.get_response(200, {
        "task_id": task_id,
        "cross_post_state": getattr(task, "cross_post_state", None),
        "cross_post_results": getattr(task, "cross_post_results", None),
        "cross_post_error": getattr(task, "cross_post_error", None),
    })


# ---------------------------------------------------------
# Autopilot System Endpoints
# ---------------------------------------------------------

class AutopilotToggleRequest(BaseModel):
    enabled: bool


@router.get("/saas/autopilot/status", summary="Consultar status do motor Autopilot")
def get_autopilot_status(request: Request):
    """Retorna se o motor Autopilot está rodando, perfis ativos e próximo agendamento."""
    from app.services.autopilot import autopilot_engine
    return utils.get_response(200, autopilot_engine.get_status())


@router.post("/saas/autopilot/toggle", summary="Ativar ou desativar o motor Autopilot")
def toggle_autopilot(body: AutopilotToggleRequest, request: Request):
    """Liga ou desliga o motor em segundo plano do Autopilot."""
    from app.services.autopilot import autopilot_engine
    autopilot_engine.set_global_enabled(body.enabled)
    return utils.get_response(200, autopilot_engine.get_status())


@router.get("/saas/autopilot/profiles", summary="Listar perfis do Autopilot")
def get_autopilot_profiles(request: Request):
    """Retorna todos os perfis de canais automatizados configurados."""
    from app.services.autopilot import autopilot_engine
    return utils.get_response(200, autopilot_engine.get_profiles())


@router.post("/saas/autopilot/profiles", summary="Salvar perfil do Autopilot")
def save_autopilot_profile(body: Dict[str, Any], request: Request):
    """Cria ou atualiza um perfil de automação do Autopilot."""
    from app.services.autopilot import autopilot_engine
    saved = autopilot_engine.save_profile(body)
    return utils.get_response(200, saved)


@router.delete("/saas/autopilot/profiles/{profile_id}", summary="Excluir perfil do Autopilot")
def delete_autopilot_profile(profile_id: str, request: Request):
    """Exclui um perfil do Autopilot pelo seu identificador."""
    from app.services.autopilot import autopilot_engine
    deleted = autopilot_engine.delete_profile(profile_id)
    if not deleted:
        return utils.get_response(404, message=f"Perfil {profile_id} não encontrado.")
    return utils.get_response(200, {"deleted": True, "id": profile_id})


@router.post("/saas/autopilot/trigger/{profile_id}", summary="Disparar execução imediata de um perfil")
def trigger_autopilot_profile(
    profile_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    sync: bool = Query(False, description="Executar de forma síncrona aguardando o resultado"),
):
    """Força a execução imediata de um perfil do Autopilot."""
    from app.services.autopilot import autopilot_engine
    profiles = autopilot_engine.get_profiles()
    profile = next((p for p in profiles if p.get("id") == profile_id), None)
    if not profile:
        return utils.get_response(404, message=f"Perfil {profile_id} não encontrado.")

    if sync:
        try:
            result = autopilot_engine.execute_profile_run(profile_id)
            return utils.get_response(200, result)
        except Exception as e:
            return utils.get_response(500, message=f"Erro na execução do autopilot: {str(e)}")
    else:
        background_tasks.add_task(autopilot_engine.execute_profile_run, profile_id)
        return utils.get_response(
            200,
            {
                "message": f"Execução do perfil '{profile.get('name')}' disparada com sucesso em segundo plano.",
                "profile_id": profile_id,
                "status": "processing",
            },
        )


@router.get("/saas/autopilot/history", summary="Histórico de execuções do Autopilot")
def get_autopilot_history(request: Request):
    """Retorna as últimas 50 execuções do Autopilot com status e postagens sociais."""
    from app.services.autopilot import autopilot_engine
    return utils.get_response(200, autopilot_engine.get_history())



