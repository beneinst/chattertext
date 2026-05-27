# Script generato da ChatterText v3.0
# Stile: narrativa  |  Pause Naturali: True  |  Noise gate: -50.0dB
# RMS target: -18.0dB  |  Pause scale: 1.00x  |  Pulizia aggressiva: False
import os,re,sys,random,torch,torchaudio as ta,pathlib,time
if sys.platform=='win32':
    import io
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
    sys.stderr=io.TextIOWrapper(sys.stderr.buffer,encoding='utf-8',errors='replace')
if torch.cuda.is_available():
    DEVICE=torch.device('cuda')
    print(f'GPU {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory//(1024**3)}GB)')
else:
    DEVICE=torch.device('cpu')
    print('CPU (nessuna GPU)')
_olt=torch.load
def _sl(*a,**k):
    if DEVICE.type=='cpu': k.setdefault('map_location',torch.device('cpu'))
    return _olt(*a,**k)
torch.load=_sl
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
print('Caricamento modello...')
model=ChatterboxMultilingualTTS.from_pretrained(device=DEVICE.type)
print('Modello su {}!'.format(DEVICE.type.upper()))
chunks=[
  "[V1_serio]\nAdesso,[p1] erano in quattro nella sala delle casseforti,[p1]\nattorno al cadavere.[b]\n\nIl Questore era accorso come si trovava,[p1]\ncon un leggero soprabito chiaro sopra il pigiama da notte,[p1]\nsui calzoni del quale aveva infilato un paio di pantaloni neri.[p2]\nCol bavero rialzato,[p1]\nin quella stanza[p1] che prendeva aria da una piccola finestra,[p1]\nil pover'uomo si sentiva soffocare[p1] e sudava.[b]\n\nNon era neppure mezzanotte,[p1]\nma lui andava a coricarsi presto,[p1]\nin una città come San Remo,[p1]\ndove di solito non accadeva mai nulla.[b]\n[/V1_serio]",
  "[V1_malinconico]\nI suoi profondi occhi buoni erano pieni di tristezza[p1]\ndavanti a quel disgraziato[p1] che avevano ucciso.[p2]\nUn uomo di oltre cinquant'anni,[p1] ancora forte,[p1] magro,[p1]\ninterminabilmente lungo,[p1]\nvisto così disteso in terra,[p2]\ncoi capelli tutti bianchi.[b]\n[/V1_malinconico]",
  "[V4_triste]\nAveva tre figli.[b]\n[/V4_triste]",
  "[V3_serio]\nLo so.[b]\n[/V3_serio]",
  "[V1_serio]\nE alzò lo sguardo verso De Vincenzi,[p1]\nche gli stava di fronte,[p1] al di là del morto.[b]\n[/V1_serio]",
  "[V3_serio]\nLa serie continua.[p2]\nè il secondo,[p1] e forse il terzo,[p1] che uccidono.[b]\n[/V3_serio]",
  "[V1_calmo]\nDe Vincenzi fece un gesto.[b]\n\nInginocchiato in mezzo a loro,[p1]\nil dottore osservava il cadavere.[p2]\nAveva scoperto il petto dell'ucciso[p1]\ne si vedeva il pugnale piantato fino al manico nella carne,[p1]\ntra le costole superiori,[p1] sopra la mammella sinistra.[b]\n\nSollevò il capo verso il Questore.[b]\n[/V1_calmo]",
  "[V5_serio]\nIl colpo è stato vibrato dal basso in alto.[p2]\nChi lo ha inferto doveva avere una statura assai inferiore a quella dell'ucciso.[b]\n[/V5_serio]",
  "[V2_deciso]\nUn metro e cinquantacinque al massimo.[b]\n[/V2_deciso]",
  "[V1_calmo]\nTutti si voltarono verso di lui con un moto di sorpresa.[b]\n[/V1_calmo]",
  "[V3_calmo]\nCome lo sa.[b]\n[/V3_calmo]",
  "[V2_deciso]\nl'ho veduto.[p2]\nLo potrei riconoscere.[p2]\nPerò lei,[p1] dottore,[p1]\nestragga il pugnale con tutte le precauzioni necessarie[p1]\na non far scomparire le impronte.[p2]\nè molto difficile che quell'uomo abbia pensato di mettersi i guanti.[b]\n[/V2_deciso]",
  "[V1_calmo]\nIl dottore osservò l'impugnatura dell'arma,[p1]\nche era liscia,[p1] lucida,[p1] di legno e acciaio,[p1]\ne scosse il capo.[b]\n[/V1_calmo]",
  "[V5_calmo]\nNon credo che si troveranno impronte.[p2]\nSe non aveva i guanti,[p1]\ndeve essersi ravvolta la mano con un fazzoletto.[b]\n[/V5_calmo]",
  "[V1_serio]\nSi alzò.[p2]\nAndò a prendere la busta dei ferri[p1] che aveva deposta sulla scrivania,[p1]\nla aprì[p1] e ne trasse una pinza.[p2]\nTornò a chinarsi sul cadavere[p1]\ned estrasse il pugnale,[p1]\nafferrandolo con la pinza[p1] sotto l'impugnatura,[p1]\nal principio della lama.[p2]\nSi vide che era una specie di coltello basco,[p1]\na serramanico,[p1] piuttosto piccolo e leggero,[p1]\nma duro e diritto,[p1] affilatissimo.[p2]\nIl medico lo depose accanto alla busta dei ferri.[b]\n\nPoi si volse al Questore,[p1]\nindicando col capo il corpo in terra.[b]\n[/V1_serio]",
  "[V5_calmo]\nLo può far portare via,[p1] se vuole.[p2]\nFarò l'autopsia domattina,[p1] all'ospedale.[p2]\nPer quanto ci sia poco da scoprire.[p2]\nLa lama ha toccato il cuore.[b]\n[/V5_calmo]",
  "[V1_calmo]\nIl Questore fece un cenno all'agente[p1]\nche si teneva sulla porta di fronte,[p1]\ne quello scomparve giù per la scala.[b]\n\nIl direttore,[p1] alto,[p1] piuttosto pingue,[p1]\ncol volto glabro e infantile[p1]\nsotto un cranio che cominciava a perdere i capelli[p1]\ne appariva troppo bianco e lucido[p1]\ntra le rade ciocche ravviate e appiccicate con la brillantina,[p1]\nera evidentemente sconvolto.[b]\n[/V1_calmo]",
  "[V4_preoccupato]\nMa perché,[p1] poi.[p2]\nPerché.[b]\n[/V4_preoccupato]",
  "[V1_calmo]\nE guardò le porte d'acciaio delle cinque casseforti,[p1]\nche erano chiuse.[b]\n[/V1_calmo]",
  "[V4_preoccupato]\nNon hanno rubato nulla.[b]\n[/V4_preoccupato]",
  "[V2_deciso]\nDottore.[p2]\nDottore,[p1] ha esaminato quest'altro.[b]\n[/V2_deciso]",
  "[V1_calmo]\nE indicava Kiergine,[p1]\nche avevano disteso sopra un divano di pelle presso alla scrivania,[p1]\ne che teneva sempre gli occhi chiusi,[p1]\nper quanto il respiro gli si fosse fatto più forte[p1]\ne quasi regolare.[b]\n[/V1_calmo]",
  "[V5_calmo]\nSì.[p2]\nHa ricevuto un colpo al mento.[p2]\nUn uppercut magistrale,[p1]\nsomministrato a regola d'arte,[p1] come sul ring.[p2]\nl'uomo che gliel'ha dato deve intendersene[p1]\ne,[p1] poiché questo qui non era allenato[p1]\ne non ha resistenza,[p1]\nlo ha mandato nel paese dei sogni per un tempo piuttosto lungo.[p2]\nGli faccia fare impacchi freddi[p1]\ne cerchi di rianimarlo col cognac.[p2]\nPoi domattina chiami un medico,[p2]\npuò darsi che,[p1] tornato in sé,[p1]\nabbia bisogno di un'iniezione.[b]\n[/V5_calmo]",
  "[V1_calmo]\nDe Vincenzi lo aveva ascoltato.[p2]\nSi guardò attorno,[p1] poi disse al Questore.[b]\n[/V1_calmo]",
  "[V2_deciso]\nQui non c'è più altro da fare e da vedere.[p2]\nSe crede,[p1]\nlo faccio trasportare in albergo.[p2]\nAnch'io ho bisogno di andarvi.[b]\n[/V2_deciso]",
  "[V1_calmo]\nE prese per un braccio il direttore.[b]\n[/V1_calmo]",
  "[V3_calmo]\nSu nelle sale,[p1] si sono accorti di nulla.[b]\n[/V3_calmo]",
  "[V4_calmo]\nNon credo.[p2]\nl'inserviente,[p1] che è venuto a chiamarmi,[p1]\nha avuto l'intelligenza di parlare a me solo[p1]\ne nessuno ha udito.[p2]\nEccolo lì.[b]\n[/V4_calmo]",
  "[V1_calmo]\nE indicò la marsina gallonata e le polpe bianche,[p1]\nche mettevano una nota di colore sotto l'atrio della scala.[p2]\nIl giovanotto era visibilmente turbato[p1]\ne non capì neppure che si parlava di lui.[p2]\nLa corsa dietro a De Vincenzi[p1] e quel cadavere[p1]\nlo avevano tratto con troppa violenza improvvisa[p1]\ndalle sue placide abitudini,[p1]\nperché potesse ancora rendersi conto di nulla.[b]\n[/V1_calmo]",
  "[V1_serio]\nAnche De Vincenzi si avvicinò al direttore del Casino.[b]\n[/V1_serio]",
  "[V2_calmo]\nLei rimane sempre nelle sale durante il giuoco.[b]\n[/V2_calmo]",
  "[V4_calmo]\nNon sempre.[p2]\nCi sono gli ispettori.[p2]\nIo faccio un giro,[p1] di tanto in tanto.[p2]\nQuando accade qualcosa,[p2]\nsa.[p2]\nGiuocatori che chiedono un prestito,[p1]\nqualcuna delle frequentatrici di mestiere[p1]\nche occorre tenere a freno,[p1]\nqualche tipo strano che solleva incidenti.[b]\n[/V4_calmo]",
  "[V2_calmo]\nDi modo che non conosce neppure di vista i frequentatori.[b]\n[/V2_calmo]",
  "[V4_calmo]\nSe non hanno avuto a che fare con me.[p2]\nMa gli ispettori hanno il dovere di osservare i giuocatori uno per uno[p1]\ne li conoscono tutti.[b]\n[/V4_calmo]",
  "[V2_deciso]\nLi interrogherò domani.[b]\n[/V2_deciso]",
  "[V1_calmo]\nDalla scala del giardino tornava l'agente[p1]\nche il Questore aveva mandato a chiamare la lettiga.[p2]\nLo seguivano due infermieri dell'ospedale.[b]\n[/V1_calmo]",
  "[V1_calmo]\nI due uomini in uniforme grigia si rimisero il berretto,[p1]\nche si erano tolto entrando,[p1]\ne si chinarono a sollevare il morto.[p2]\nPoco dopo sparivano giù dalla scala[p1]\ncol loro funebre fardello.[b]\n[/V1_calmo]",
  "[V2_calmo]\nHo pensato[p1]\nche è meglio lasciare qui Kiergine[p1]\nfin quando non si sia rimesso.[p2]\nVoi,[p1]\nfategli i bagnoli sul volto[p1]\ne cercate di fargli bere un po' di cognac.[p2]\nIl dottore vi manderà un suo collega[p1]\ne aspetterete me,[p1] domattina.[p2]\nLei,[p1] dottore,[p1]\nvuole incaricarsi di far venire qui un medico[p1]\na vedere quest'uomo.[b]\n[/V2_calmo]",
  "[V5_calmo]\nCi deve essere quello di turno alla farmacia.[b]\n[/V5_calmo]",
  "[V1_calmo]\nIl Questore si avviò per la scala,[p1]\nseguito da De Vincenzi[p1]\ne dal sanitario con la sua busta nera.[p2]\nIl direttore salì per l'altra scala e scomparve.[b]\n\nl'agente,[p1] rimasto davanti al divano dove giaceva il russo,[p1]\nguardò l'inserviente[p1]\nche si era mosso appena per lasciare il passo al direttore.[b]\n[/V1_calmo]",
  "[V6_ironico]\nDove posso trovare l'acqua,[p1]\nun asciugatoio,[p1]\nil cognac.[p2]\nAnche da infermiere mi tocca fare.[b]\n[/V6_ironico]",
  "[V6_calmo]\nC'è il lavabo sul primo pianerottolo,[p1] salendo.[p2]\nE il cognac vado a prenderglielo al bar.[b]\n[/V6_calmo]",
  "[V1_riflessivo]\nAppena in giardino,[p1]\nil dottore salutò in fretta i due funzionari[p1]\ne si allontanò.[b]\n\nIl Questore si fermò in mezzo al viale.[b]\n[/V1_riflessivo]",
  "[V3_preoccupato]\nLei crede che questo nuovo delitto[p1]\nsia assolutamente occasionale.[b]\n[/V3_preoccupato]",
  "[V2_riflessivo]\nPuò darsi.[p2]\nl'uomo,[p1] che aveva trascinato Kiergine[p1]\nverso il fondo del salone da giuoco,[p1]\nvoleva sfuggirmi.[p2]\nKiergine doveva avergli detto chi ero.[p2]\nUn uomo pratico della topografia del Casino,[p1] a ogni modo.[p2]\nForse,[p1] il russo si è opposto alla fuga.[p2]\nOppure l'uomo ha voluto liberarsi di lui,[p1]\nstordendolo,[p1]\ntogliendogli i sensi per qualche tempo.[p2]\nDeve conoscere l'effetto dei propri pugni.[p2]\nForse,[p1] un antico boxeur.[p2]\nl'ho osservato attentamente.[p2]\nPuò avere una quarantina d'anni,[p1]\ndeve essere fortissimo,[p1] così basso e tarchiato,[p1]\ne non credo sia italiano[p1]\na giudicare dalle linee del volto[p1]\ne dal colore atrocemente rosso della pelle.[b]\n[/V2_riflessivo]",
  "[V3_serio]\nUn delitto tanto selvaggio[p1] e così inutile.[p2]\nSe il cassiere si è opposto al suo passaggio,[p1]\nperché non lo ha colpito con un pugno,[p1]\ncome aveva fatto col russo.[b]\n[/V3_serio]",
  "[V2_riflessivo]\nDeve avere avuto le sue ragioni.[p2]\nIl cassiere,[p1] forse,[p1] lo conosceva.[b]\n[/V2_riflessivo]",
  "[V3_calmo]\nPuò darsi.[p2]\nE lei ha dato i connotati a Racheli.[b]\n[/V3_calmo]",
  "[V2_calmo]\nSì.[p2]\nMa alla stazione non lo prenderanno.[p2]\nSe è fuggito,[p1] come credo,[p1]\ndeve averlo fatto in auto.[p2]\nA meno che non abbia qualche rifugio a San Remo[p1]\no nei dintorni.[b]\n[/V2_calmo]",
  "[V3_malinconico]\nE adesso.[b]\n[/V3_malinconico]",
  "[V3_riflessivo]\nC'è da aspettare soltanto che il russo rinvenga.[p2]\nDomattina lo faremo parlare.[b]\n[/V3_riflessivo]",
  "[V1_calmo]\nDe Vincenzi trasalì.[b]\n[/V1_calmo]",
  "[V2_gentile]\nCommendatore,[p1]\nse mi permette,[p1]\nvorrei rivolgerle una preghiera.[b]\n[/V2_gentile]",
  "[V3_calmo]\nDica.[p2]\nMa so già di che si tratta.[p2]\nLei vuol condurre l'inchiesta da solo[p1]\ne ha paura che noi,[p1] intervenendo,[p1] le roviniamo tutto.[p2]\nDel resto,[p1] può aver ragione.[p2]\nChi arrischia di più in questo affare è lei.[p2]\nMa domattina arriverà il giudice istruttore da Imperia.[b]\n[/V3_calmo]",
  "[V2_deciso]\nLo so.[p2]\nEd è per questo che vorrei riuscire a qualche cosa[p1]\nquesta notte.[b]\n[/V2_deciso]",
  "[V2_riflessivo]\nNon so.[p2]\nMa all'albergo Europa non ho ancora interrogato nessuno.[p2]\nPuò darsi che qualcosa ne esca.[b]\n[/V2_riflessivo]",
  "[V3_calmo]\nE da noi che cosa vuole.[b]\n[/V3_calmo]",
  "[V2_deciso]\nChe cerchino,[p1] se lei crede,[p1] l'assassino di questa sera.[p2]\nDeve pur avere lasciato qualche traccia.[p2]\nSe si trovava a San Remo da qualche tempo,[p1]\ne certo è così,[p1]\nnon può non essersi fatto vedere per la città.[p2]\nE dentro il Casino.[p2]\nPer le trattorie,[p1] nei caffè.[p2]\nPuò darsi che avesse qualche compagno.[b]\n[/V2_deciso]",
  "[V3_preoccupato]\nCrede che si tratti di una banda.[p2]\nUn affare di spionaggio,[p1] allora,[p2]\nproprio come suppongono a Roma.[b]\n[/V3_preoccupato]",
  "[V2_riflessivo]\nNon so,[p1] non so.[p2]\nDi spionaggio non direi.[p2]\nSan Remo non mi sembra il posto adatto[p1]\nper un'azione di tal genere[p1]\ne in grande stile.[p2]\nPerò.[b]\n[/V2_riflessivo]",
  "[V3_calmo]\nE quel russo.[p2]\nHo fatto chiedere notizie a tutte le Polizie d'europa,[p1]\nda Varsavia a Londra.[b]\n[/V3_calmo]",
  "[V2_deciso]\nBisognerebbe telegrafare a Düsseldorf.[p2]\nLui afferma di aver parenti laggiù.[b]\n[/V2_deciso]",
  "[V3_calmo]\nA Düsseldorf,[p1] ha detto.[p2]\nLo farò.[b]\n[/V3_calmo]",
  "[V1_calmo]\nIl Questore aveva ripreso a camminare[p1]\ne De Vincenzi lo seguiva.[p2]\nQuando furono sullo spiazzo,[p1] davanti alla facciata principale,[p1]\nsi voltarono entrambi a guardare le finestre.[p2]\nAdesso le avevano aperte[p1] e c'era gente sulle terrazze.[p2]\nSi vedevano gli abiti chiari delle donne,[p1]\ngli sparati bianchi degli uomini.[b]\n[/V1_calmo]",
  "[V3_calmo]\nNon si sono accorti di nulla.[b]\n[/V3_calmo]",
  "[V2_ironico]\nè difficile che un giuocatore si accorga di qualche cosa,[p1]\nquando giuoca.[b]\n[/V2_ironico]",
  "[V3_calmo]\nè vero.[b]\n[/V3_calmo]",
  "[V1_calmo]\nTacquero.[p2]\nIl Questore tese la mano al commissario.[b]\n[/V1_calmo]",
  "[V1_malinconico]\nE scese la larga scalinata,[p1]\nappoggiandosi a uno dei bastoni di ferro[p1]\nche correvano nel mezzo.[p2]\nEra stanco.[p2]\nE soprattutto disorientato.[p2]\nNon trovava il modo di afferrare[p1]\nneppure un capo di quella matassa.[b]\n[/V1_malinconico]",
  "[V1_riflessivo]\nDe Vincenzi entrò nel vestibolo del Casino,[p1]\nandò a sedersi in una poltrona[p1]\ne trasse dalla tasca il foglio che gli aveva dato Racheli.[b]\n\nIn tutto,[p1]\ngli ospiti dell'albergo al momento del dramma erano dodici,[p1]\nsenza contare Letang,[p1] che era morto,[p1]\nPaulette Garat,[p1] che era scomparsa,[p1]\ne Kiergine.[b]\n\nSullo stesso piano di quei tragici protagonisti,[p1]\nc'erano il barone Giorgio Milesia,[p1]\ni coniugi Bertrand e Agnes Staub.[p2]\nGli altri otto abitavano al secondo e al terzo piano.[p2]\nLa signorina Rosetta Bill,[p1]\nche si era messa un nome esotico,[p1]\nma che si chiamava bonariamente Rosetta Ruzzoni,[p1]\ncon la sua accompagnatrice Carlotta Boni.[p2]\nAntonietta Stefani,[p1] sola,[p1] proveniente da Bari.[p2]\nIl levantino Epaminonda Kristopoulos.[p2]\nDue croupiers,[p1] impiegati al Casino.[p2]\nConrad van Lie,[p1] gioielliere di Amsterdam,[p1]\ne sua nipote Anny Ribens.[b]\n[/V1_riflessivo]",
  "[V1_serio]\nTolti i due croupiers,[p1]\ni quali erano fuori discussione,[p1]\nrimanevano dieci persone da interrogare.[p2]\nDe Vincenzi scartò pure dal giuoco[p1]\nRosetta Ruzzoni e Antonietta Stefani[p1]\ne mise un gran punto interrogativo[p1]\naccanto al nome del gioielliere olandese e di sua nipote.[p2]\nRimanevano in pochi.[b]\n\nUno almeno di tutti costoro[p1]\ndoveva necessariamente avere qualcosa a che vedere[p1]\ncon la morte di Letang,[p1]\nse non anche con la scomparsa di Paulette Garat[p1]\ne con la pozza di sangue nel canotto.[b]\n[/V1_serio]",
  "[V1_riflessivo]\nPoteva dirsi con sicurezza[p1]\nche a uccidere il giovane francese[p1]\nera stato un ospite dell'albergo[p1]\no per lo meno un complice di uno degli ospiti.[p2]\nAltrimenti,[p1] nell'entrare in albergo e nell'uscirne,[p1]\nl'assassino non sarebbe passato inosservato[p1]\nalmeno al portiere.[p2]\nNé alcuno aveva mai detto[p1]\nche Letang avesse ricevuto quella sera un visitatore,[p1]\ne certo una tale indicazione[p1]\nsarebbe stata la prima[p1]\nche il personale dell'albergo avrebbe data,[p1]\nappena scoperto l'assassinio.[b]\n[/V1_riflessivo]",
  "[V1_calmo]\nSollevò gli occhi[p1]\ne vide che i lifts e un paio di camerieri lo osservavano.[p2]\nRimise in tasca il foglio[p1] e si alzò.[b]\n\nDi dietro alle tende di velluto,[p1]\nveniva sempre la musica del jazz.[b]\n\nSi avvicinò a un cameriere.[b]\n[/V1_calmo]",
  "[V2_calmo]\nC'è gente al dancing.[b]\n[/V2_calmo]",
  "[V2_calmo]\nE chi è la tedesca.[b]\n[/V2_calmo]",
  "[V2_calmo]\nGrazie.[b]\n[/V2_calmo]",
  "[V1_riflessivo]\nIl dancing,[p1] con quella luce opalina,[p1]\ntraslucida,[p1] madreperlacea,[p1]\ndiffusa sul tappeto rosso[p1]\ne sui tavoli[p1]\ne alle pareti pesantemente addobbate di velluto giallo,[p1]\nsembrava un acquario con pochi pesci.[b]\n\nI tavoli erano quasi tutti vuoti[p1]\ne sulla pedana giravano un paio di coppie.[b]\n\nDe Vincenzi sedette al primo tavolo accanto alla porta.[p2]\nAccorse un cameriere,[p1]\nche lo guardava con disapprovazione[p1]\npel suo vestito chiaro.[p2]\nOrdinò qualche sandwich e una birra.[p2]\nEra la una passata[p1] e aveva fame.[p2]\nSapeva che quella notte non si sarebbe coricato.[b]\n[/V1_riflessivo]",
  "[V1_calmo]\nIl cameriere gli si tolse davanti,[p1] allontanandosi,[p1]\ne lui allora poté vedere Agnes Staub.[p2]\nLa riconobbe subito dalle gemme.[p2]\nE anche l'avrebbe riconosciuta senza quelle.[p2]\nEra un tipo,[p1] Agnes Staub.[b]\n\nUn poco troppo star,[p1]\nun poco troppo vamp da film supergiallo o di spionaggio,[p2]\nma non poteva dirsi che non fosse riuscita nel suo genere.[p2]\nPortava i capelli divisi in mezzo al capo[p1]\ne ricadenti come due ali chiuse,[p1]\nali d'oro bianco,[p1]\nattorno al volto pieno,[p1] dalle linee sicuramente segnate.[p2]\nDue occhi immensi,[p1] neri,[p1] magnetici,[p2]\nil naso dalle nari aperte,[p1] carnose,[p1] vibranti,[p2]\nla bocca lunga,[p1] troppo lunga,[p1] forse,[p1] sensualissima,[p2]\nil mento tondo.[b]\n[/V1_calmo]",
  "[V1_riflessivo]\nIl corpo alto e pieno[p1]\nrisultava in ogni sua curva così fasciato[p1]\nda un abito di seta nera lucida,[p1]\nchiuso attorno al collo[p1]\ne spaccato poi in profondità alle spalle,[p1]\nsicché la schiena,[p1]\nattraverso quel triangolo,[p1]\nsi mostrava nuda,[p1] arcuata,[p1] nervosa.[b]\n\nE sul petto,[p1] dal collo,[p1]\nle scendeva una collana di brillanti tutti uguali,[p1]\naccesi di mille fuochi.[p2]\nAttorno ai polsi,[p1]\nle maniche dell'abito erano fermate[p1]\nda altri due cerchi di brillanti.[b]\n\nSeduta,[p1] mostrava fino al ginocchio le gambe[p1]\ncon le calze di seta carnicina,[p1]\ntalmente sottile[p1]\nche De Vincenzi le credette nude.[b]\n[/V1_riflessivo]",
  "[V1_calmo]\nGirava attorno sguardi inquisitori,[p1] leggermente drammatici.[p2]\nEra troppo manifestamente misteriosa,[p1]\nper avere in sé un mistero.[p2]\nEppure,[p1] colpiva.[b]\n\nSi alzò di scatto[p1] con un colpo delle reni da cavallina di sangue[p1]\ne l'uomo,[p1] che le sedeva a lato,[p1] la imitò subito.[b]\n\nDoveva aver sentito su di sé[p1]\nl'attenzione scrutatrice di De Vincenzi.[p2]\nCertamente,[p1] i loro sguardi si erano incrociati[p1]\ne quelli della donna avevano balenato[p1]\ncon impercettibile inquietudine.[p2]\nO era soltanto interesse per lo sconosciuto.[b]\n[/V1_calmo]",
  "[V1_riflessivo]\nAdesso ballava,[p1]\ne De Vincenzi cercò invano nuovamente il suo sguardo.[p2]\nElla mostrava di ignorare completamente[p1]\nche a quel tavolo isolato,[p1] ben visibile nel suo abito da viaggio,[p1]\nsedesse un giovane ignoto[p1] che la fissava.[b]\n\nCivetteria.[p2]\nDisdegno.[p2]\nAtteggiamento professionale.[b]\n[/V1_riflessivo]",
  "[V1_calmo]\nl'uomo che la teneva tra le braccia,[p1]\nsfiorandole appena una spalla e le reni,[p1]\npoteva aver quarant'anni,[p1] era bruno,[p1]\ncon la pelle olivastra,[p1]\ngli occhi troppo neri,[p1] infossati,[p2]\nun turco,[p1] un greco[p1] o qualcosa di simile.[p2]\nLa sua eleganza non poteva essere di peggior gusto.[p2]\nIl bottone allo sparato,[p1]\nun'acquamarina contornata di brillantini,[p1]\nappariva immenso,[p2]\nle scarpe di copale avevano la punta inverosimilmente sottile,[p2]\ni risvolti triangolari dello smoking sembravano due vele[p1]\ned erano lucidi come specchi.[p2]\nLa mano che poggiava sulle reni della donna[p1]\nmetteva in mostra quattro anelli,[p1]\ncon gemme di tutti i colori.[b]\n[/V1_calmo]",
  "[V1_riflessivo]\nMa il corpo ancora agile e flessibile di quell'uomo,[p1]\ncertamente maturo,[p1]\nsi muoveva ballando con impeccabile estetica[p1]\ne con leggerezza felina.[p2]\nUn levantino[p1]\ndoveva essere adusato alla danza[p1]\ncome a tutti i giuochi acrobatici,[p1]\nper istinto di razza.[p2]\nCiò non impediva,[p1] del resto,[p1]\nche avesse il collo corto,[p1]\nle spalle a baule[p1] e il ventre rotondo.[b]\n\nGuardava vagamente davanti a sé,[p1] sulla spalla della donna,[p1]\ncon occhi fissi e immoti,[p1]\ncome paralizzati da qualche stupefacente.[b]\n[/V1_riflessivo]",
  "[V1_calmo]\nLa musica tacque.[p2]\nAgnes Staub,[p1] invece di tornare al tavolo,[p1]\nsi diresse alla porta,[p1]\nmormorando qualche parola al suo compagno,[p1]\nche trasse un foglio da cento dalla tasca dei pantaloni[p1]\ne lo porse al cameriere,[p1]\naccorso a inchinarsi al loro passaggio.[b]\n\nDe Vincenzi non si mosse.[p2]\nNon li guardò neppure,[p1] mentre uscivano.[p2]\nMangiava un sandwich.[b]\n\nIl senso di vuoto nella sala era aumentato.[b]\n[/V1_calmo]",
  "[V1_riflessivo]\nA un tavolo poco distante da quello di De Vincenzi,[p1]\nuna inglese cinquantenne,[p1]\ncon la bocca contorta,[p1] una spalla più alta dell'altra,[p1]\nteneva le mani sulle ginocchia di un giovanotto[p1]\nseduto davanti a lei[p1]\ne gli parlava,[p1]\nfissandolo con occhi acquosi,[p1] verdi,[p1]\nbalenanti di riflessi metallici.[p2]\nE il giovanotto,[p1] un ballerino del dancing,[p1] evidentemente,[p1]\nle sorrideva in modo tanto amabile,[p1]\nda apparire osceno.[b]\n[/V1_riflessivo]",
  "[V1_calmo]\nLentamente,[p1] De Vincenzi si alzò.[p2]\nPagò l'ammontare.[p2]\nPrese il cappello,[p1] che aveva deposto accanto a sé,[p1]\naprì le tende,[p1] uscì nel vestibolo.[b]\n[/V1_calmo]",
  "[V1_calmo]\nC'era sempre il cameriere loquace,[p1]\nche,[p1] quando lo vide,[p1]\ngli sorrise,[p1] quasi per ammiccargli.[b]\n\nLui gli si avvicinò.[b]\n[/V1_calmo]",
  "[V2_calmo]\nLa tedesca è salita.[b]\n[/V2_calmo]",
  "[V2_calmo]\nGrazie.[b]\n[/V2_calmo]",
  "[V1_calmo]\nE fece per uscire,[p1]\nma nel voltarsi[p1]\nvide l'impiegato delle tessere[p1]\nche gli faceva dei segni da lontano[p1]\ne correva verso di lui.[p2]\nLo attese.[b]\n[/V1_calmo]",
  "[V6_preoccupato]\nIl direttore la cerca,[p1] commissario.[p2]\nHa bisogno di parlarle.[b]\n[/V6_preoccupato]",
  "[V2_calmo]\nPerché.[b]\n[/V2_calmo]",
  "[V6_preoccupato]\nSembra che dalla cassa,[b]\n[/V6_preoccupato]",
  "[V2_calmo]\nEbbene.[b]\n[/V2_calmo]",
  "[V6_preoccupato]\nUna prima verifica soltanto,[p1]\ndopo la morte del capo cassiere.[b]\n[/V6_preoccupato]",
  "[V2_calmo]\nEbbene.[b]\n[/V2_calmo]",
  "[V1_calmo]\nDe Vincenzi non diede alcun segno di meraviglia.[p2]\nFissò il giovane,[p1]\nche sembrava invaso dal panico.[b]\n[/V1_calmo]",
  "[V2_calmo]\nGliel'ha detto il direttore.[b]\n[/V2_calmo]",
  "[V2_calmo]\nE che mancano due milioni[p1]\nchi glielo ha detto.[b]\n[/V2_calmo]",
  "[V1_ironico]\nChissà perché sul volto del commissario[p1]\naleggiava un sorriso ironico.[b]\n[/V1_ironico]",
  "[V2_calmo]\nVedo che lei è bene informato.[p2]\nVenga qui.[b]\n[/V2_calmo]",
  "[V1_calmo]\nLo trasse fuori,[p1] all'aperto,[p1]\nsi appoggiò con la schiena alla balaustrata,[p1]\nsi era messe le mani in tasca.[b]\n\nLa notte era calda,[p1] ma limpida.[p2]\nLe strade,[p1] sotto di loro,[p1] erano deserte[p1]\ne,[p1] così illuminate,[p1]\nil senso di desolazione che davano[p1]\nappariva maggiore.[p2]\nDalle finestre aperte del primo piano,[p1] sopra le loro teste,[p1]\nveniva sempre il rumore metallico,[p1] continuo,[p1] uniforme[p1]\ndei gettoni agitati[p1]\ne a tratti,[p1] scandite,[p1]\nle frasi monotone dei croupiers.[b]\n[/V1_calmo]",
  "[V2_deciso]\nMi dica,[p1] adesso,[p1] quel che ha saputo.[b]\n[/V2_deciso]",
  "[V2_riflessivo]\nDa dove mancano i due milioni.[p2]\nMa perché poi proprio due milioni esatti.[b]\n[/V2_riflessivo]",
  "[V6_calmo]\nNella cassaforte,[p1]\ni fogli da mille vengono riposti a pacchi di cento ognuno.[p2]\nMancano venti pacchi.[b]\n[/V6_calmo]",
  "[V2_riflessivo]\nHo capito.[p2]\nE la cassaforte si trova[p1]\nnella camera dove hanno ucciso Valeri.[b]\n[/V2_riflessivo]",
  "[V6_calmo]\nSì.[b]\n[/V6_calmo]",
  "[V2_riflessivo]\nNon si fugge,[p1] portando via venti pacchi di biglietti da mille.[p2]\nl'involto è grosso.[p2]\nE poi tutti gli sportelli delle casseforti erano chiusi.[p2]\nCome si sono accorti dell'ammanco.[b]\n[/V2_riflessivo]",
  "[V6_calmo]\nOgni notte fanno la verifica del denaro[p1]\nche si trova in cassa.[b]\n[/V6_calmo]",
  "[V2_calmo]\nNo,[p1] non ogni notte.[p2]\nSoltanto di quello che è stato consegnato ai tavoli da giuoco[p1]\ne agli changeurs.[p2]\nIl controllo viene operato soprattutto[p1]\nsulle varie dotazioni di fiches.[b]\n[/V2_calmo]",
  "[V6_calmo]\nA che ora si fa questo controllo.[b]\n[/V6_calmo]",
  "[V2_calmo]\nAlla chiusura,[p1] dopo le quattro del mattino.[b]\n[/V2_calmo]",
  "[V6_calmo]\nE questa notte.[b]\n[/V6_calmo]",
  "[V2_calmo]\nAvvenuto l'assassinio,[p1]\nil direttore ha voluto procedere a una verifica generale[p1]\ndel denaro in cassa.[b]\n[/V2_calmo]",
  "[V2_riflessivo]\nAllora,[p1]\ni due milioni potevano mancare[p1]\nanche prima che uccidessero il capo cassiere.[b]\n[/V2_riflessivo]",
  "[V2_ironico]\nNaturalmente.[b]\n[/V2_ironico]",
  "[V1_calmo]\nSi voltarono,[p1]\nperché sentirono dalla scalinata il passo affrettato di due persone[p1]\nche salivano.[b]\n\nUn uomo e una donna.[p2]\nTanto l'uno che l'altra passarono,[p1]\nsenza vedere De Vincenzi e l'impiegato.[p2]\nCorrevano,[p1] quasi.[p2]\nl'uomo procedeva con le spalle curve[p1]\ne la testa piegata da un lato.[p2]\nAveva il collo del soprabito nero rialzato,[p1]\nil cappello duro sugli occhi.[p2]\nLa donna,[p1] grassa,[p1] dipinta,[p1] ossigenata,[p1]\nera ravvolta in un mantello da sera[p1]\ne non portava cappello.[p2]\nAnsava per la salita fatta.[b]\n\nScomparvero nell'interno[p1]\ndirigendosi verso il fondo.[b]\n[/V1_calmo]",
  "[V6_calmo]\nè il signor Baracca,[p1] il consigliere delegato.[b]\n[/V6_calmo]",
  "[V2_calmo]\nE la signora.[b]\n[/V2_calmo]",
  "[V6_calmo]\nSua moglie.[b]\n[/V6_calmo]",
  "[V1_riflessivo]\nDe Vincenzi tacque.[p2]\nSi voltò a guardare in basso.[p2]\ndall'altra parte della strada,[p1]\nil portone dell'albergo Europa rimaneva chiuso,[p1]\nsotto la tettoia a vetri.[p2]\nUn gruppo di uomini uscì dal Casino,[p1]\nscese la scalinata,[p1] proseguì pei viali.[p2]\nParlavano a voce alta.[b]\n[/V1_riflessivo]",
  "[V6_calmo]\nTre volte il ventisette.[b]\n[/V6_calmo]",
  "[V7_malinconico]\nSe tenevo la serie.[b]\n[/V7_malinconico]",
  "[V1_calmo]\nQuando furono sulla strada,[p1]\nuno di essi salutò gli altri[p1]\ne si diresse verso l'albergo.[p2]\nSuonò.[p2]\nSi aprì la porticina tagliata in uno dei battenti[p1]\ne gli si richiuse alle spalle.[b]\n\nDe Vincenzi guardò l'orologio.[p2]\nErano le due.[b]\n[/V1_calmo]",
  "[V2_deciso]\nSta bene.[p2]\nNon dica che mi ha trovato.[p2]\nE non mi cerchi neppure in albergo,[p1]\nperché le farei dire che non ci sono.[p2]\nVedrò il direttore domattina.[p2]\nPer i due milioni c'è tempo.[b]\n[/V2_deciso]",
  "[V1_riflessivo]\nE scese la scalinata,[p1]\nlasciando l'altro immobile dallo stupore.[b]\n[/V1_riflessivo]"
]
AUDIO_V1="2.Voci/1pier.wav"
AUDIO_V2="2.Voci/1RobertoCofini.wav"
AUDIO_V3="2.Voci/1Liber.wav"
AUDIO_V4="2.Voci/1Romano.wav"
AUDIO_V5="2.Voci/1PasqualeR-N.wav"
AUDIO_V6="2.Voci/1Giovanni-N.wav"
AUDIO_V7="2.Voci/2LauraT.wav"
HAS2=True
HAS3=True
HAS4=True
HAS5=True
HAS6=True
HAS7=True
for p,lbl,en in [(AUDIO_V1,'V1',True),(AUDIO_V2,'V2',HAS2),(AUDIO_V3,'V3',HAS3),(AUDIO_V4,'V4',HAS4),(AUDIO_V5,'V5',HAS5),(AUDIO_V6,'V6',HAS6),(AUDIO_V7,'V7',HAS7)]:
    if en and not os.path.exists(p): print(f'NON TROVATO [{lbl}]: {p}'); exit(1)
EPRESET={
    "calmo": {
        "exaggeration": 0.35,
        "cfg_weight": 0.85,
        "temperature": 0.4,
        "top_p": 0.75,
        "min_p": 0.15
    },
    "appassionato": {
        "exaggeration": 0.75,
        "cfg_weight": 0.6,
        "temperature": 0.65,
        "top_p": 0.8,
        "min_p": 0.1
    },
    "arrabbiato": {
        "exaggeration": 0.9,
        "cfg_weight": 0.5,
        "temperature": 0.75,
        "top_p": 0.85,
        "min_p": 0.08
    },
    "triste": {
        "exaggeration": 0.45,
        "cfg_weight": 0.8,
        "temperature": 0.45,
        "top_p": 0.7,
        "min_p": 0.18
    },
    "ironico": {
        "exaggeration": 0.65,
        "cfg_weight": 0.65,
        "temperature": 0.7,
        "top_p": 0.82,
        "min_p": 0.12
    },
    "sussurrato": {
        "exaggeration": 0.25,
        "cfg_weight": 0.9,
        "temperature": 0.35,
        "top_p": 0.65,
        "min_p": 0.2
    },
    "riflessivo": {
        "exaggeration": 0.4,
        "cfg_weight": 0.78,
        "temperature": 0.48,
        "top_p": 0.72,
        "min_p": 0.16
    },
    "deciso": {
        "exaggeration": 0.8,
        "cfg_weight": 0.55,
        "temperature": 0.6,
        "top_p": 0.78,
        "min_p": 0.1
    },
    "preoccupato": {
        "exaggeration": 0.55,
        "cfg_weight": 0.72,
        "temperature": 0.55,
        "top_p": 0.74,
        "min_p": 0.14
    },
    "gentile": {
        "exaggeration": 0.42,
        "cfg_weight": 0.82,
        "temperature": 0.42,
        "top_p": 0.7,
        "min_p": 0.16
    },
    "serio": {
        "exaggeration": 0.5,
        "cfg_weight": 0.75,
        "temperature": 0.5,
        "top_p": 0.73,
        "min_p": 0.15
    },
    "solenne": {
        "exaggeration": 0.55,
        "cfg_weight": 0.8,
        "temperature": 0.38,
        "top_p": 0.68,
        "min_p": 0.2
    },
    "estatico": {
        "exaggeration": 0.85,
        "cfg_weight": 0.52,
        "temperature": 0.72,
        "top_p": 0.88,
        "min_p": 0.07
    },
    "malinconico": {
        "exaggeration": 0.48,
        "cfg_weight": 0.82,
        "temperature": 0.43,
        "top_p": 0.7,
        "min_p": 0.18
    },
    "vibrante": {
        "exaggeration": 0.88,
        "cfg_weight": 0.48,
        "temperature": 0.78,
        "top_p": 0.9,
        "min_p": 0.06
    },
    "intimo": {
        "exaggeration": 0.3,
        "cfg_weight": 0.88,
        "temperature": 0.36,
        "top_p": 0.65,
        "min_p": 0.22
    }
}
DEF_P={'exaggeration':0.62,'cfg_weight':0.7,'temperature':0.58,'top_p':0.75,'min_p':0.15}
PAUSE_SCALE=1.0
NOISE_GATE_DB=-50.0
RMS_TARGET_DB=-18.0
TRIM_DB=-45.0
AGGRESSIVE_CLEAN=False
NATURAL_PAUSES=True

def pauses_to_natural_text(text):
    """
    v3.0 - Converte tag pausa in punteggiatura naturale + newline reali.
    Chatterbox usa i newline come guide respiratorie: ogni riga = unità di respiro.
    """
    PTABLE = {
        "[metro]":("",0),"[enjambement]":("",0),
        "[p1]":(",",1),"[verso]":(",",1),"[cesura]":(",",1),
        "[p2]":(".",1),"[pausa]":(".",1),
        "[p3]":(".",2),"[b]":(".",2),"[strofa]":(".",2),"[pausa_lunga]":(".",2),
        "[bd]":(".",3),"[cap]":(".",3),"[silenzio]":(".",3),
    }
    ORDER=["[silenzio]","[cap]","[bd]","[pausa_lunga]","[strofa]","[b]",
           "[p3]","[pausa]","[p2]","[cesura]","[verso]","[p1]","[enjambement]","[metro]"]
    for tag in ORDER:
        if tag not in PTABLE: continue
        punct,nlcount=PTABLE[tag]
        ph="__PNLT__{}__NL{}__".format(punct.replace(".","DOT").replace(",","COMMA"),nlcount)
        text=re.sub(re.escape(tag),ph,text,flags=re.IGNORECASE)
    def resolve(m):
        rp=m.group(1).replace("DOT",".").replace("COMMA",",")
        nl="\n"*int(m.group(2))
        pos=m.start(); before=text[:pos].rstrip()
        if rp and before and before[-1] in ".,!?:;": return nl if nl else " "
        return (rp+nl) if rp else (nl if nl else " ")
    text=re.sub(r"__PNLT__([\w]*)__NL(\d)__",resolve,text)
    text=re.sub(r"\n{4,}","\n\n\n",text)
    text=re.sub(r"[ \t]+\n","\n",text)
    text=re.sub(r"\n[ \t]+","\n",text)
    text=re.sub(r"([.,!?])\s*([.,])",r"\1",text)
    text=re.sub(r"[ \t]{2,}"," ",text)
    text=re.sub(r" +([,.])\n",r"\1\n",text)
    text=re.sub(r" +([,.])\s*$",r"\1",text)
    return text.strip()

PM={
    '[p1]':(0.18,0.03), '[p2]':(0.40,0.05), '[p3]':(0.65,0.07),
    '[b]': (1.00,0.10), '[bd]':(1.60,0.15), '[cap]':(2.00,0.20),
    '[pausa]':(0.50,0.05),'[pausa_lunga]':(1.20,0.10),'[silenzio]':(2.00,0.15),
    '[verso]':(0.30,0.04),'[strofa]':(1.20,0.12),'[metro]':(0.08,0.01),
    '[enjambement]':(0.05,0.01),'[cesura]':(0.45,0.05),
}
def gp(tag):
    b,s=PM.get(tag.lower(),(0.40,0.05))
    b=b*PAUSE_SCALE
    raw=random.gauss(b,s*PAUSE_SCALE)
    return max(b*0.60, min(raw, b*1.40))
JM={'[join]':(0.00,'overlap'),'[cont]':(0.12,'smooth'),
    '[cambio]':(0.50,'cambio'),'[cambio3]':(0.50,'cambio'),
    '[cambio4]':(0.50,'cambio'),'[cambio5]':(0.50,'cambio'),
    '[cambio6]':(0.50,'cambio'),'[cambio7]':(0.50,'cambio'),
    '[para]':(0.90,'silence'),'[stacco]':(1.40,'fade_sil_fade'),
    '[lungo]':(1.80,'fade_sil_fade'),'[scena]':(2.40,'hard'),
    '[dissolvenza]':(1.60,'fade_sil_fade')}
EP={'e1':{'exaggeration_delta':0.10,'cfg_weight_delta':-0.05},'e2':{'exaggeration_delta':0.25,'cfg_weight_delta':-0.12},'ep':{'exaggeration_delta':0.15,'cfg_weight_delta':-0.08}}
EN=r"calmo|appassionato|arrabbiato|triste|ironico|sussurrato|riflessivo|deciso|preoccupato|gentile|serio|solenne|estatico|malinconico|vibrante|intimo"
PR=re.compile(r'(\[p[123]\]|\[b(?:d)?\]|\[cap\]|\[pausa(?:_lunga)?\]|\[silenzio\]|\[verso\]|\[strofa\]|\[metro\]|\[enjambement\]|\[cesura\])',re.IGNORECASE)
ER=re.compile(r'\[e[12p]\]',re.IGNORECASE)
JR=re.compile(r'\[(?:join|cont|cambio|cambio3|cambio4|cambio5|cambio6|cambio7|para|stacco|lungo|scena|dissolvenza)\]',re.IGNORECASE)
def pc(chunk):
    rp=PR.findall(chunk)
    ps=[(p,gp(p)) for p in rp]; tp=sum(d for _,d in ps)
    et=ER.findall(chunk); ek=et[-1].lower().strip('[]') if et else None
    jt=JR.findall(chunk); jk=jt[-1].lower() if jt else None
    # si_meta: rimuove SOLO tag voce/emozione/enfasi/giunzioni
    # LASCIA i tag pausa [p1][p2][b]... intatti: servono a prepare_text_for_tts()
    def si_meta(t):
        t=ER.sub('',t); t=JR.sub('',t); return t.strip()
    # si_voice: rimuove anche i tag voce dal testo pulito
    def si_voice(t):
        t=re.sub(r'\[/?(?:v1|v2|v3|v4|v5|v6|v7)(?:_'+EN+r')?\]','',t,flags=re.IGNORECASE)
        return si_meta(t)
    m=re.search(r'\[(v1|v2|v3|v4|v5|v6|v7)_(' +EN+r')\]',chunk,re.IGNORECASE)
    if m:
        v,e=m.group(1).lower(),m.group(2).lower()
        cl=re.sub(r'\[(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\]','',chunk,flags=re.IGNORECASE)
        cl=re.sub(r'\[/(?:v1|v2|v3|v4|v5|v6|v7)_(?:'+EN+r')\]','',cl,flags=re.IGNORECASE)
        return si_meta(cl),v,e,ps,tp,ek,jk
    m=re.search(r'\[(v1|v2|v3|v4|v5|v6|v7)\]',chunk,re.IGNORECASE)
    if m:
        v=m.group(1).lower()
        cl=re.sub(r'\[/?(?:v1|v2|v3|v4|v5|v6|v7)\]','',chunk,flags=re.IGNORECASE)
        return si_meta(cl),v,None,ps,tp,ek,jk
    m=re.search(r'\[('+EN+r')\]',chunk,re.IGNORECASE)
    if m:
        e=m.group(1).lower()
        cl=re.sub(r'\[(?:'+EN+r')\]','',chunk,flags=re.IGNORECASE)
        cl=re.sub(r'\[/(?:'+EN+r')\]','',cl,flags=re.IGNORECASE)
        return si_meta(cl),'v1',e,ps,tp,ek,jk
    return si_meta(chunk),'v1',None,ps,tp,ek,jk
def pp(emo,ek=None):
    p=EPRESET[emo].copy() if emo and emo in EPRESET else DEF_P.copy()
    p.setdefault('top_p',0.75); p.setdefault('min_p',0.15)
    if ek and ek in EP:
        p['exaggeration']=min(1.0,p['exaggeration']+EP[ek]['exaggeration_delta'])
        p['cfg_weight']=max(0.1,p['cfg_weight']+EP[ek]['cfg_weight_delta'])
    return p
tc=[pc(c) for c in chunks]
def noise_gate(wav, sr, gate_db=NOISE_GATE_DB, hpz=80, attack_ms=8, release_ms=60):
    thr=10**(gate_db/20)
    if wav.dim()==1: wav=wav.unsqueeze(0)
    wav=ta.functional.highpass_biquad(wav, sr, cutoff_freq=hpz)
    env=torch.abs(wav[0])
    att=int(sr*attack_ms/1000); rel=int(sr*release_ms/1000)
    gate=torch.zeros_like(env)
    g=0.0
    for i in range(len(env)):
        if env[i]>thr: target=1.0
        else: target=0.0
        if target>g: g=g+(1.0-g)/max(1,att)
        else: g=g*(1.0-1.0/max(1,rel))
        gate[i]=g
    wav=wav*gate.unsqueeze(0)
    return wav
def rms_normalize(wav, target_db=RMS_TARGET_DB):
    if wav.dim()==1: wav=wav.unsqueeze(0)
    rms=torch.sqrt(torch.mean(wav**2)+1e-8)
    target_rms=10**(target_db/20)
    gain=target_rms/rms; gain=min(gain, 10.0)
    wav=wav*gain
    wav=torch.tanh(wav*0.9)*1.1
    return wav.clamp(-0.98, 0.98)
def declick(wav, sr, window_ms=3):
    w=int(sr*window_ms/1000)
    if w<2 or wav.shape[-1]<w*2: return wav
    kern=torch.ones(1,1,w)/w
    smoothed=torch.nn.functional.conv1d(wav.float().unsqueeze(0), kern, padding=w//2).squeeze(0)
    diff=torch.abs(wav-smoothed)
    thr=diff.mean()*3.0
    mask=(diff>thr).float()
    k2=int(sr*1/1000)+1
    if k2%2==0: k2+=1
    k2=torch.ones(1,1,k2)/k2
    mask=torch.nn.functional.conv1d(mask.unsqueeze(0),k2,padding=k2.shape[-1]//2).squeeze(0).clamp(0,1)
    return wav*(1-mask)+smoothed*mask
def trim_silence(wav, sr, threshold_db=TRIM_DB, pad_ms=30):
    thr=10**(threshold_db/20)
    mg=int(sr*pad_ms/1000)
    mo=wav[0] if wav.dim()>1 else wav; en=torch.abs(mo)
    indices=(en>thr).nonzero(as_tuple=True)[0]
    if len(indices)==0: return wav
    s=max(0, indices[0].item()-mg); e=min(len(en), indices[-1].item()+mg)
    return wav[...,s:e]
def apply_fade(wav, sr, fade_ms=14):
    f=int(sr*fade_ms/1000); wav=wav.clone()
    wav[...,:f]*=torch.linspace(0,1,f)
    wav[...,-f:]*=torch.linspace(1,0,f)
    return wav
def full_process(wav, sr):
    wav=noise_gate(wav, sr)
    if AGGRESSIVE_CLEAN: wav=declick(wav, sr)
    wav=trim_silence(wav, sr)
    wav=apply_fade(wav, sr)
    wav=rms_normalize(wav)
    return wav
def prepare_text_for_tts(txt):
    '''
    v3.0: se NATURAL_PAUSES attivo, converte i tag pausa in
    punteggiatura + newline reali PRIMA di passare a model.generate().
    I tag enfasi/giunzioni vengono rimossi (già usati in parametri).
    '''
    if NATURAL_PAUSES:
        txt = pauses_to_natural_text(txt)
    else:
        # Vecchio comportamento: rimuovi solo i tag pausa senza conversione
        txt = re.sub(r'\[(?:p[123]|b(?:d)?|cap|pausa(?:_lunga)?|silenzio|verso|strofa|metro|enjambement|cesura)\]','',txt,flags=re.IGNORECASE)
    # Rimuovi eventuali tag residui (enfasi, giunzioni) che non devono andare al TTS
    txt = re.sub(r'\[e[12p]\]','',txt,flags=re.IGNORECASE)
    txt = re.sub(r'\[(?:join|cont|cambio|cambio3|cambio4|cambio5|cambio6|cambio7|para|stacco|lungo|scena|dissolvenza)\]','',txt,flags=re.IGNORECASE)
    return txt.strip()
segs=[]; fail=[]
st=time.time()
print('\n'+'='*55)
print('AVVIO GENERAZIONE [{}]'.format(DEVICE.type.upper()))
print('Pause Naturali: {}'.format('ATTIVE' if NATURAL_PAUSES else 'disattive'))
print('='*55)
for i,(txt,vo,em,ps,tp,ek,jk) in enumerate(tc):
    if i>0:
        el=time.time()-st; av=el/i; rm=av*(len(tc)-i)
        eta='  ETA:{:.0f}s'.format(rm)
    else: eta=''
    pct=int(i/len(tc)*100)
    bar=chr(9608)*(pct//5)+chr(9617)*(20-pct//5)
    _em_s='['+em+']' if em else ''
    _ek_s='['+ek+']' if ek else ''
    _jk_s='['+jk.strip('[]')+']' if jk else ''
    _tail='...' if len(txt)>80 else ''
    _rep=repr(txt[:80])
    print('\n [{}] {}%{}'.format(bar,pct,eta))
    print(' Chunk {}/{} [{}]{}{}{}'.format(i+1,len(tc),vo.upper(),_em_s,_ek_s,_jk_s))
    print('   {}{}'.format(_rep,_tail))
    if tp>0: print('   pausa audio: {:.2f}s (gauss x{:.2f})'.format(tp, PAUSE_SCALE))
    if len(txt.split())<5: print('   ATTENZIONE: chunk corto!')
    tts_txt = prepare_text_for_tts(txt)
    if NATURAL_PAUSES and tts_txt != txt:
        _nl_count = tts_txt.count('\n')
        print('   Testo TTS ({} righe natural):'.format(_nl_count+1))
        for _ln in tts_txt[:120].split('\n'):
            if _ln.strip(): print('     |', _ln.strip()[:70])
    if   vo=='v7' and HAS7: vp=AUDIO_V7
    elif vo=='v6' and HAS6: vp=AUDIO_V6
    elif vo=='v5' and HAS5: vp=AUDIO_V5
    elif vo=='v4' and HAS4: vp=AUDIO_V4
    elif vo=='v3' and HAS3: vp=AUDIO_V3
    elif vo=='v2' and HAS2: vp=AUDIO_V2
    else:                   vp=AUDIO_V1
    p=pp(em,ek); ok=False
    try:
        wav=model.generate(tts_txt,language_id='it',audio_prompt_path=vp,
            exaggeration=p['exaggeration'],cfg_weight=p['cfg_weight'],
            temperature=p['temperature'],min_p=p['min_p'],top_p=p['top_p'])
        if DEVICE.type=='cuda': wav=wav.cpu()
        wav=full_process(wav, model.sr)
        if tp>0:
            sil=torch.zeros((wav.shape[0],int(model.sr*tp)))
            wav=torch.cat([wav,sil],dim=-1)
        segs.append(wav); ok=True; print('   OK!')
    except Exception as e: print('   ERR:{} retry...'.format(e))
    if not ok:
        try:
            wav=model.generate(tts_txt,language_id='it',audio_prompt_path=vp,
                exaggeration=0.0,cfg_weight=0.25,temperature=0.22,min_p=0.20,top_p=0.65)
            if DEVICE.type=='cuda': wav=wav.cpu()
            wav=full_process(wav, model.sr)
            segs.append(wav); print('   Recuperato!')
        except Exception as e2: print(f'   FALLITO:{e2}'); fail.append(i)
if not segs: print('Nessun audio.'); exit(1)
od=pathlib.Path('1.Output'); od.mkdir(exist_ok=True)
num=len(list(od.glob('audiolibro_*.wav')))+1
out=od/'audiolibro_{:02d}.wav'.format(num)
SCENE=[
        "poi" ,"quando" ,"all'improvviso" ,"improvvisamente" ,"in quel momento" ,"mentre" ,"subito dopo" ,"intanto" ,"nel frattempo" ,"a quel punto" ,"alla fine"
    ]
DIALOG=[
        "disse" ,"penso" ,"grido" ,"urlo" ,"sussurro" ,"domando" ,"rispose" ,"chiese" ,"mormoro" ,"esclamo" ,"borbotto" ,"annuncio" ,"replico" ,"aggiunse" ,"continuo" ,"riprese"
    ]
EMOW=[
        "paura" ,"orrore" ,"ansia" ,"terrore" ,"pianto" ,"felice" ,"gioia" ,"triste" ,"disperato" ,"sconvolto" ,"agitato" ,"sorpreso" ,"commosso" ,"morte" ,"vita" ,"anima" ,"silenzio" ,"infinito" ,"luce" ,"buio" ,"voce" ,"cuore" ,"sogno"
    ]
CONCS=[
        "tuttavia" ,"eppure" ,"nonostante" ,"al contrario" ,"invece" ,"d'altra parte" ,"in realta" ,"in verita" ,"dunque" ,"quindi" ,"pertanto" ,"di conseguenza"
    ]
REFL=[
        "forse" ,"chissa" ,"davvero" ,"possibile che" ,"si chiese" ,"si domando" ,"aveva senso" ,"non aveva senso" ,"significava" ,"voleva dire"
    ]
PHIL=[
        "verita" ,"giustizia" ,"anima" ,"essere" ,"nulla" ,"infinito" ,"eternita" ,"ragione" ,"sapienza" ,"virtu" ,"bene" ,"male" ,"conoscenza" ,"ignoranza" ,"logos"
    ]
def dyn_pause(txt, emo=None):
    t=txt.strip(); lo=t.lower(); ln=len(t); lc=t[-1:] if t else ''
    if t.endswith('...'): base,sig=1.50,0.15
    elif lc in '?!':     base,sig=1.00,0.12
    elif lc=='.':        base,sig=0.42,0.06
    elif lc==':':        base,sig=0.70,0.08
    elif lc==';':        base,sig=0.60,0.07
    elif lc==',':        base,sig=0.20,0.03
    else:                base,sig=0.18,0.03
    if ln>500:   base*=1.50
    elif ln>300: base*=1.30
    elif ln>150: base*=1.12
    elif ln<60:  base*=0.80
    if any(lo.startswith(s) for s in SCENE):  base*=1.28
    if any(w in lo for w in PHIL):            base*=1.45
    if any(w in lo for w in CONCS):           base*=1.38
    if any(w in lo for w in REFL):            base*=1.30
    if any(w in lo for w in EMOW):            base*=1.18
    if any(v in lo for v in DIALOG):          base*=0.75
    if emo in ('riflessivo','calmo','triste','preoccupato','malinconico','solenne'): base*=1.18
    elif emo in ('arrabbiato','deciso','vibrante'):                                 base*=0.72
    elif emo in ('sussurrato','intimo'):                                            base*=1.10
    base=base*PAUSE_SCALE
    raw=random.gauss(base, sig*PAUSE_SCALE)
    return max(base*0.60, min(raw, base*1.40))
def cf(s1,s2,sr,fms=55):
    f=int(sr*fms/1000)
    if s1.shape[-1]<f or s2.shape[-1]<f: return torch.cat([s1,s2],dim=-1)
    fo=torch.linspace(1,0,f)**1.5; fi=torch.linspace(0,1,f)**1.5
    return torch.cat([s1[...,:-f],s1[...,-f:]*fo+s2[...,:f]*fi,s2[...,f:]],dim=-1)
def ov(s1,s2,sr,oms=80):
    f=int(sr*oms/1000)
    if s1.shape[-1]<f or s2.shape[-1]<f: return torch.cat([s1,s2],dim=-1)
    fo=torch.linspace(1,0,f)**2; fi=torch.linspace(0,1,f)**2
    return torch.cat([s1[...,:-f],s1[...,-f:]*fo+s2[...,:f]*fi,s2[...,f:]],dim=-1)
def fsf(s1,s2,sr,ss,foms=80,fims=60):
    fl=int(sr*foms/1000); il=int(sr*fims/1000)
    sl=max(0,int(sr*ss)-fl-il)
    s1=s1.clone()
    if s1.shape[-1]>=fl: s1[...,-fl:]*=torch.linspace(1.0,0.0,fl)**1.8
    sil=torch.zeros((s2.shape[0],sl),dtype=s2.dtype)
    s2=s2.clone()
    if s2.shape[-1]>=il: s2[...,:il]*=torch.linspace(0.0,1.0,il)**1.8
    return torch.cat([s1,sil,s2],dim=-1)
def asmb(s1,s2,sr,jt):
    if jt is None: return None
    ss,mode=JM.get(jt,(0.5,'silence'))
    ss=ss*PAUSE_SCALE
    if mode=='overlap': return ov(s1,s2,sr)
    if mode=='fade_sil_fade': return fsf(s1,s2,sr,ss)
    sil=torch.zeros((s2.shape[0],int(sr*ss))) if ss>0 else None
    if mode=='smooth': s2w=torch.cat([sil,s2],dim=-1) if sil is not None else s2; return cf(s1,s2w,sr,fms=30)
    if mode=='cambio': s2w=torch.cat([sil,s2],dim=-1) if sil is not None else s2; return cf(s1,s2w,sr,fms=100)
    if mode=='silence': s2w=torch.cat([sil,s2],dim=-1) if sil is not None else s2; return cf(s1,s2w,sr,fms=55)
    if mode=='hard': return torch.cat([s1,sil,s2],dim=-1) if sil is not None else torch.cat([s1,s2],dim=-1)
    return cf(s1,s2,sr)
jl=[x[6] for x in tc]
fa=None
for i,seg in enumerate(segs):
    if fa is None: fa=seg; continue
    jt=jl[i-1]; res=asmb(fa,seg,model.sr,jt)
    if res is None:
        pau=dyn_pause(chunks[i-1], emo=tc[i-1][2])
        sil=torch.zeros((seg.shape[0],int(model.sr*pau)))
        fa=cf(fa,torch.cat([sil,seg],dim=-1),model.sr)
        js='auto({:.2f}s)'.format(pau)
    else: fa=res; js=jt if jt else 'auto'
    print(f'   -> join {i}: {js}')
fa=rms_normalize(fa)
ta.save(out,fa,model.sr)
dur=fa.shape[-1]/model.sr; tot=time.time()-st
print(f'\n FILE: {out}')
print(f'   Durata: {dur:.1f}s ({dur/60:.1f} min)')
print(f'   Tempo:  {tot:.1f}s ({tot/60:.1f} min)')
print(f'   Device: {DEVICE.type.upper()}')
print(f'   Pause Naturali: {"ATTIVE" if NATURAL_PAUSES else "disattive"}')
voci_attive=[('V2',HAS2),('V3',HAS3),('V4',HAS4),('V5',HAS5),('V6',HAS6),('V7',HAS7)]
voci_str=' | '.join(n for n,a in voci_attive if a) or '-'
print(f'   Voci: V1 + {voci_str}')
print(f'   OK: {len(segs)}/{len(chunks)}')
if fail: print(f'   FAIL: {fail}')
print('\nProcesso completato!')
print('__CHATTERTEXT_DONE__')