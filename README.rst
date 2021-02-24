.. SPDX-FileCopyrightText: Magenta ApS
..
.. SPDX-License-Identifier: MPL-2.0

.. _SD_MOX:

SD_MOX
======

SD-MOX er en udvidelse til SD-løn, som leveres af Silkeborg Data. SD-Mox muliggør 
opdatering af visse felter på organisationsenheder, som findes både i OS2MO
og i SD-løn.

OS2MO's integration til SD-mox involverer brug af SD-løns AMQP-kø
til afsendelse af ændringer og oprettelser, hvorimod læsning og verifikation foregår
via SD's webinterface.

Integrationen er synkron, udført med triggere (se https://os2mo.readthedocs.io/en/latest/api/triggers.html#customization-and-triggers),
således at forstå at man får svar umiddelbart i forbindelse med sin handling, som er en af

1. oprettelse af organisatiorisk enhed
2. omdøbning af organisatorisk enhed
3. flytning af organisatorisk enhed
4. ændring/oprettelse af adresser på en organisatorisk enhed


.. _SD_MOX_konfiguration:

Konfiguration
-------------

Konfiguration af modulet er fleksibel og dermed lidt kompleks. For det første
er der url, bruger og password mv. til SD's webinterface som dokumenteret under
`SD løn opsætning`_ . SD's AMQP-opsætning er derimod specifik for SD-mox-modulet 
og udgøres af disse settings:

 * ``integrations.SD_Lon.sd_mox.AMQP_USER``: AMQP bruger aftalt med SD
 * ``integrations.SD_Lon.sd_mox.AMQP_HOST``: AMQP host aftalt med SD
 * ``integrations.SD_Lon.sd_mox.AMQP_PORT``: AMQP port aftalt med SD
 * ``integrations.SD_Lon.sd_mox.AMQP_PASSWORD``: AMQP password aftalt med SD
 * ``integrations.SD_Lon.sd_mox.AMQP_CHECK_RETRIES``: Antal gange man prøver at validere de via AMQP overførte ændringer (default: 6)
 * ``integrations.SD_Lon.sd_mox.AMQP_CHECK_WAITTIME``: Ventetid før hvert forsøg på validering (default: 3)
 * ``integrations.SD_Lon.sd_mox.VIRTUAL_HOST``: Virtuel host aftalt med SD

Dernæst beskriver ``integrations.SD_Lon.sd_mox.TRIGGERED_UUIDS`` en liste af 
UUID-strenge for afdelinger på topniveau, som, inklusive undertræer, anses som 
forbundet med SD. Den kan se ud som ``["e3e38b32-61c0-4900-a200-000001510002"]``,
flere strenge adskilles af komma.

SD-løn anvender et begreb, som hedder NY-Niveauer, disse er reguleret sådan at man kan
sætte en afdeling på ``Afdelings-niveau`` ind under en afdeling på ``NY1-niveau``, men 
ikke omvendt. ``integrations.SD_Lon.sd_mox.OU_LEVELKEYS`` beskriver en liste af 
NY-niveauer i rækkefølge fra højere til lavere niveauer. Denne liste anvendes til at
omsætte os2mos klasse-uuider for facetten ``org_unit_level`` til de tekst-strenge som 
SD-MOX forventer samt for at validere omtalte regler inden indsætning. Den ser 
typisk ud som ``["NY6-niveau", "NY5-niveau",... ,"NY1-niveau", "Afdelings-niveau"]``

Nogle kommuner anvender en facet, der hedder ``time_planning``, og den setting, 
der hedder ``integrations.SD_Lon.sd_mox.OU_TIME_PLANNING_MO_VS_SD`` udgør en mapning
imellem brugervendte nøgler for klasserne i ``time_planning`` og de strenge, der skal 
overføres til SD som repræsentation for samme. Den kan se ud som :
``{..., "DannesIkke": "Normaltjeneste dannes ikke"}``


Anvendelse af SD-mox 
--------------------

Når man i OS2MOS grafiske klient arbejder med organisatoriske enheder i et undertræ,
der er inkluderet i ``integrations.SD_Lon.sd_mox.TRIGGERED_UUIDS``, vil flytninger,
oprettelser, omdøbninger og tilføjelse/ændring af adresser bliver overført til SD. 
Der er dog visse begræsninger i input, som gennemgås nedenfor. 

Der er en forsinkelse på 8.5 sekunder i brugerinterfacet mellem afsendelse imod SD
og modtagelse af kvitteringen for ændringerne. Det er ikke SD, som har den forsinkelse; 
Den er indført i OS2MO fordi vi ikke får kvitteringen for ændringen direkte fra SD,
men først ser den via at opslag på webinterfacet, og ei er nødt til at vente til vi 
forventer at SD er faldet til ro efter en ændring.

Begrænsninger i input
---------------------

Der er en del begrænsninger i input, som er indført enten ud fra viden om SD’s krav eller
slet og ret ved at prøve sig frem. Alle disse begrænsninger gælder kun i de OS2MO-undertræer, 
som er inkluderet i ``integrations.SD_Lon.sd_mox.TRIGGERED_UUIDS``

 * Afdelingsnumre skal være med stort. Det er de hos SD.

 * Pnumre efter addresser. Det interface vi anvender hos SD kan kun vise Pnumre
   hvis der er en postadresse – derfor har vi indført et krav om postadresse, 
   hvis man angiver Pnummer.

 * Afdelingsnumre skal være 2 til 4 karakterer lange i SD - denne begrænsning understøttes
   af SD-MOX

 * Ny Niveauer har ikke-tilladte forældre-barn-relationer, og der valideres inden vi forsøger
   at sætte noget ind hos SD. 


SD-mox fejlmeddelelser
----------------------

Der er en del mulige fejl, man kan begå, når man anvender OS2MO med denne integration tilkoblet.
Der er gjort et stort arbejde for at fange dem, så man ikke kan lave en ændring i OS2MO,
der ikke er reflekteret i SD. Der vises fejlmeddelser i OS2MO's brugerinterface for at gøre 
opmærksom på dem og de er alle foranstillet prefixet ``Integrationsfejl, SD-Mox:``

 * SD AMQP credentials mangler
 * Klasse-uuider for conf af Ny-Niveauer eller Tidsregistrering mangler
 * Uventet svar fra SD amqp
 * Startdato skal altid være den første i en måned
 * Afdeling ikke unik. Code {}, uuid {}, level {}
 * Enhedsnummer for kort
 * Enhedsnummer for langt
 * Ugyldigt tegn i enhedsnummer
 * Enhedsnummer skal være store bogstaver
 * Enhedsnummer er i brug
 * Forældrenheden findes ikke
 * Enhedstypen passer ikke til forældreenheden
 * Afdeling ikke fundet: %s
 * Følgende felter kunne ikke opdateres i SD
 * Enhedstype er ikke et kendt NY-niveau
 * Forældreenhedens enhedstype er ikke et kendt NY-niveau
 * Opret postaddresse før pnummer

