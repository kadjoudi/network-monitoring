from prometheus_client import start_http_server, Gauge
import time
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus Gauge for device status
# Mapping: dormant=0, online=1, alerting=2, offline=3
status_gauge = Gauge(
    'meraki_device_status',
    'Device status (0 - dormant, 1 - online, 2 - alerting, 3 - offline)',
    ['serial', 'name', 'networkId', 'productType', 'model', 'orgName', 'orgId']
)

# Prometheus Gauges for uplink loss and latency
uplink_loss_gauge = Gauge(
    'meraki_device_uplink_loss',
    'Uplink packet loss in percentage',
    ['serial', 'networkId', 'uplink', 'ip', 'orgName', 'orgId']
)
uplink_latency_gauge = Gauge(
    'meraki_device_uplink_latency',
    'Uplink latency in milliseconds',
    ['serial', 'networkId', 'uplink', 'ip', 'orgName', 'orgId']
)

# Gauge to track request processing time
request_processing_seconds = Gauge(
    'request_processing_seconds',
    'Total processing time for metrics collection'
)

def collect_device_status_metrics():
    # Fetch configuration from environment variables
    organization_id = os.getenv('MERAKI_ORG_ID')
    api_key = os.getenv('MERAKI_API_KEY')
    
    if not organization_id or not api_key:
        logger.error("MERAKI_ORG_ID and MERAKI_API_KEY environment variables must be set.")
        return
    
    # Define API endpoints
    status_url = f'https://api.meraki.com/api/v1/organizations/{organization_id}/devices/statuses'
    uplink_url = f'https://api.meraki.com/api/v1/organizations/{organization_id}/devices/uplinksLossAndLatency'
    
    # Set up headers
    headers = {
        'X-Cisco-Meraki-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Parameters for device status API
    params = {
        'perPage': 1000  # Maximum allowed per page for status
        # Add other query parameters here if needed, e.g., 'statuses': 'online,offline'
    }
    
    start_time = time.time()
    
    try:
        # Fetch device statuses from the Meraki API
        response = requests.get(status_url, headers=headers, params=params)
        response.raise_for_status()
        devices = response.json()
        
        logger.info(f"Fetched {len(devices)} devices from device status API.")
        
        # Fetch organization details
        org_url = f'https://api.meraki.com/api/v1/organizations/{organization_id}'
        org_response = requests.get(org_url, headers=headers)
        org_response.raise_for_status()
        organization_data = org_response.json()
        
        org_name = organization_data.get('name', 'Unknown')
        org_id = organization_data.get('id', 'Unknown')
        
        # Process each device for status metrics
        for device in devices:
            serial = device.get('serial', 'Unknown')
            name = device.get('name', device.get('mac', 'Unknown'))
            network_id = device.get('networkId', 'Unknown')
            product_type = device.get('productType', 'Unknown')
            model = device.get('model', 'Unknown')  # Label for device model
            status_str = device.get('status', 'unknown').lower()
            
            # Map status string to integer
            status_mapping = {
                'dormant': 0,
                'online': 1,
                'alerting': 2,
                'offline': 3
            }
            status = status_mapping.get(status_str, -1)  # -1 for unknown statuses
            
            # Update the Prometheus gauge for status
            status_gauge.labels(
                serial=serial,
                name=name,
                networkId=network_id,
                productType=product_type,
                model=model,
                orgName=org_name,
                orgId=org_id
            ).set(status)
        
        logger.info("Device status metrics updated successfully.")
        
        # Collect uplink loss and latency metrics
        uplink_params = {
            'timespan': 300  # 5 minutes lookback period
        }
        
        uplink_response = requests.get(uplink_url, headers=headers, params=uplink_params)
        uplink_response.raise_for_status()
        uplink_data = uplink_response.json()
        
        logger.info(f"Fetched {len(uplink_data)} uplink data points from uplink loss and latency API.")
        
        # Process uplink loss and latency
        for uplink in uplink_data:
            serial = uplink.get('serial', 'Unknown')
            network_id = uplink.get('networkId', 'Unknown')
            uplink_interface = uplink.get('uplink', 'Unknown')
            ip = uplink.get('ip', 'Unknown')
            time_series = uplink.get('timeSeries', [])
            
            if not time_series:
                logger.warning(f"No time series data for device {serial} uplink {uplink_interface}")
                continue  # Skip to the next uplink
            
            # Assume the last entry is the latest data point
            latest_data_point = time_series[-1]
            loss = latest_data_point.get('lossPercent', 0.0)
            latency = latest_data_point.get('latencyMs', 0.0)
            
            # Update Prometheus gauges for uplink loss and latency
            uplink_loss_gauge.labels(
                serial=serial,
                networkId=network_id,
                uplink=uplink_interface,
                ip=ip,
                orgName=org_name,
                orgId=org_id
            ).set(loss)
            
            uplink_latency_gauge.labels(
                serial=serial,
                networkId=network_id,
                uplink=uplink_interface,
                ip=ip,
                orgName=org_name,
                orgId=org_id
            ).set(latency)
        
        logger.info("Uplink loss and latency metrics updated successfully.")
    
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")  # For HTTP errors
    except Exception as e:
        logger.error(f"Error fetching device statuses or uplink data: {e}")  # For other errors
    
    finally:
        processing_time = time.time() - start_time
        request_processing_seconds.set(processing_time)
        logger.info(f"Metrics collection completed in {processing_time:.2f} seconds.")

if __name__ == '__main__':
    # Start Prometheus HTTP server on port 9090
    start_http_server(9090)
    logger.info("Prometheus metrics server started on port 9090")
    
    # Initial metrics collection
    collect_device_status_metrics()
    
    # Schedule metrics collection every 60 seconds
    while True:
        time.sleep(60)
        collect_device_status_metrics()
