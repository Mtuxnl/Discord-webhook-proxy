# Discord Webhook Proxy voor Matrix Hookshot

Een lichtgewicht middleware-applicatie die Discord-geformatteerde webhooks vertaalt naar HTML-berichten die compatibel zijn met [Matrix Hookshot](https://github.com/matrix-org/matrix-hookshot).

Deze proxy zorgt ervoor dat rijke "embeds"—inclusief filmposters, achtergronden, statusvelden en kleuren—prachtig worden weergegeven in Matrix-clients (zoals Element). Het bootst hierbij de originele Discord "Card" layout na, inclusief de donkere achtergrond en correcte uitlijning.

## Kenmerken

* **Rijke Embed Vertaling:** Zet Discord Embeds om naar HTML-layouts geoptimaliseerd voor Matrix.
* **Discord Styling:** Gebruikt een donker thema (#2f3136) en CSS-technieken om de look-and-feel van Discord embeds na te bootsen. (poging tot)
* **Media Proxy Ondersteuning:** Herschrijft automatisch externe afbeeldings-URL's (posters/fanart) naar een lokale beveiligde media-proxy. Dit voorkomt mixed-content waarschuwingen en zorgt dat afbeeldingen correct laden in privacy-gerichte Matrix-clients.

## Aan de slag

### Vereisten

1. Een Matrix server (Synapse/Dendrite).
2. **Matrix Hookshot** geïnstalleerd en geconfigureerd met "Generic Webhooks" ingeschakeld.
3. Docker.

### Installatie

1. git clone <https://github.com/Mtuxnl/Discord-webhook-proxy.git>
2. docker build -t discord-webhook-proxy .
3. docker run -d \\ --name discord-webhook-proxy \\ -p 5001:5001 \\ -e OUTGOING_WEBHOOK_BASE_URL="http://jouw-hookshot-url:9000/webhook" \\ -e MEDIA_PROXY_HOST="proxy-url" \\ --restart unless-stopped \\ discord-webhook-proxy

### Omgevingsvariabelen

OUTGOING_WEBHOOK_BASE_URL De basis-URL van je Hookshot instantie http://10.0.0.5:9000/webhook

MEDIA_PROXY_HOST Hostnaam van de image proxy bijvoorbeeld assets.mtux.nl

## Image Proxying

Om ervoor te zorgen dat afbeeldingen (zoals filmposters) correct en veilig worden weergegeven binnen Matrix-clients, maakt dit project gebruik van een media-proxy mechanisme. Dit voorkomt dat clients externe afbeeldingen blokkeren en zorgt ervoor dat alles via een vertrouwd domein wordt geserveerd.

De logica voor de media-handler is gebaseerd op onze **Matrix Sticker Proxy**. Je vindt de broncode en installatie-instructies voor de media-handler hier:

[**Matrix Sticker Proxy / Image Proxy**](https://github.com/Mtuxnl/Matrix-sticker-picker/tree/main/matrix-sticker-proxy)

Zorg ervoor dat de server.py uit dat project draait en bereikbaar is via de host die je hebt ingesteld als MEDIA_PROXY_HOST in deze container.

## Projectstructuur

```
.
├── app.py             # Hoofdlogica van de Flask-applicatie
├── build.sh           # Script om multi-arch Docker images te bouwen
├── Dockerfile         # Docker build configuratie
└── requirements.txt   # Python afhankelijkheden
```

## Licentie

Dit project is gelicenseerd onder de GNU Affero General Public License v3.0 (AGPL-3.0). Zie het bestand LICENSE.txt voor meer informatie.
