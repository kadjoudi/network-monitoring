# Collecte de Statistiques de Statut pour les Equipements Meraki

Ce projet collecte des métriques sur l'état des appareils Meraki, telles que la perte de paquets et la latence de liaison montante, et expose ces données sous forme de métriques Prometheus.

## Installation

1. **Clonez ce dépôt** :
    ```bash
    git clone https://github.com/kadjoudi/network-monitoring
    cd network-monitoring
    ```

2. **Créez un environnement virtuel** :
    ```bash
    python3 -m venv env
    ```

3. **Activez l'environnement virtuel** :
   - Sur **Linux/macOS** :
     ```bash
     source env/bin/activate
     ```
   - Sur **Windows** :
     ```bash
     .\env\Scripts\activate
     ```

4. **Installez les dépendances Python nécessaires** :
    ```bash
    pip install prometheus_client requests
    ```

5. **Définissez les variables d'environnement pour l'API Meraki** :
    ```bash
    export MERAKI_ORG_ID="votre_organisation_id"
    export MERAKI_API_KEY="votre_api_key"
    ```

## Configuration de Grafana Alloy

Avant d'exécuter le script, assurez-vous que votre instance Grafana Alloy est mise à jour avec les dernières configurations et ajoutez le bloc suivant à la configuration actuelle pour permettre la collecte de métriques depuis l'adresse locale par Grafana Alloy :

```hcl
prometheus.scrape "Meraki" {
  // Collect metrics from the default listen address.
  targets = [{
    __address__ = "127.0.0.1:9090",
  }]
  forward_to = [prometheus.remote_write.metrics_service.receiver]
}
```
## Utilisation

Lancez le serveur pour exposer les métriques sur le port 9090 :
```bash
python merakiapiexporter.py
```

## Métriques Exposées

- **meraki_device_status** : Statut de chaque appareil (0 - dormant, 1 - en ligne, 2 - en alerte, 3 - hors ligne).
- **meraki_device_uplink_loss** : Pourcentage de perte de paquets en liaison montante.
- **meraki_device_uplink_latency** : Latence en liaison montante (ms).
- **request_processing_seconds** : Temps total de traitement pour la collecte des métriques.

