import time
import random
import json
import boto3
import subprocess
import os
from datetime import datetime

# Load AWS IoT Configuration from JSON file
def load_aws_config():
    """Load AWS IoT configuration from aws-iot-config.json"""
    config_file = "aws-iot-config.json"
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"✅ Loaded configuration from {config_file}")
            return config
        else:
            print(f"⚠️  Configuration file {config_file} not found, using defaults")
            return None
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return None

# Load configuration
AWS_CONFIG = load_aws_config()

if AWS_CONFIG:
    AWS_IOT_ENDPOINT = AWS_CONFIG.get("endpoint")
    DEVICE_ID = AWS_CONFIG.get("client_id", "precision-agriculture-device")
    THING_NAME = AWS_CONFIG.get("thing_name", "AgricultureEdgeDevice")
    TOPICS = AWS_CONFIG.get("topics", {})
else:
    # Fallback to automatic detection
    def get_aws_iot_endpoint():
        """Automatically get AWS IoT endpoint"""
        try:
            result = subprocess.run(['aws', 'iot', 'describe-endpoint', '--endpoint-type', 'iot:Data-ATS'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                endpoint_info = json.loads(result.stdout)
                return endpoint_info['endpointAddress']
            else:
                print(f"❌ Error getting endpoint: {result.stderr}")
                return None
        except Exception as e:
            print(f"❌ Could not get AWS IoT endpoint: {e}")
            return None

    AWS_IOT_ENDPOINT = get_aws_iot_endpoint()
    DEVICE_ID = "precision-agriculture-device"
    THING_NAME = "AgricultureEdgeDevice"
    TOPICS = {
        "biometric_data": f"agriculture/edge/{THING_NAME}/biometric",
        "health_analysis": f"agriculture/fog/{THING_NAME}/health-analysis",
        "cloud_analysis": f"agriculture/cloud/{THING_NAME}/cloud-analysis",
        "emergency_alerts": f"agriculture/actuators/{THING_NAME}/emergency",
        "health_notifications": f"agriculture/actuators/{THING_NAME}/notifications"
    }

# Initialize AWS IoT client
if AWS_IOT_ENDPOINT:
    try:
        iot_client = boto3.client('iot-data', endpoint_url=f'https://{AWS_IOT_ENDPOINT}')
        print(f"✅ Connected to AWS IoT Endpoint: {AWS_IOT_ENDPOINT}")
        print(f"🔧 Device: {DEVICE_ID} | Thing: {THING_NAME}")
        print(f"📍 Region: {AWS_IOT_ENDPOINT.split('.')[2] if '.' in AWS_IOT_ENDPOINT else 'Unknown'}")
    except Exception as e:
        print(f"❌ Error initializing AWS IoT client: {e}")
        iot_client = None
else:
    print("❌ Could not initialize AWS IoT client. Please check your AWS configuration.")
    iot_client = None

# ========= Simulated IoT Sensor Data for Precision Agriculture =========
def generate_precision_agriculture_sensor_data():
    """Generate sensor data matching the iFogSim simulation sensors (GYROSCOPE, ACCELEROMETER, PROXIMITY)"""
    return {
        "GYROSCOPE": {
            "x_axis": round(random.uniform(-180.0, 180.0), 3),  # degrees
            "y_axis": round(random.uniform(-180.0, 180.0), 3),  # degrees 
            "z_axis": round(random.uniform(-180.0, 180.0), 3),  # degrees
            "angular_velocity": round(random.uniform(0.0, 10.0), 3)  # rad/s
        },
        "ACCELEROMETER": {
            "x_accel": round(random.uniform(-20.0, 20.0), 3),  # m/s²
            "y_accel": round(random.uniform(-20.0, 20.0), 3),  # m/s²
            "z_accel": round(random.uniform(-20.0, 20.0), 3),  # m/s²
            "magnitude": round(random.uniform(0.0, 25.0), 3)   # m/s²
        },
        "PROXIMITY": {
            "distance": round(random.uniform(0.0, 500.0), 2),  # cm
            "obstacle_detected": random.choice([True, False]),
            "signal_strength": round(random.uniform(0.0, 100.0), 2)  # %
        },
        "timestamp": datetime.utcnow().isoformat(),
        "sensor_transmission_time": 3.0  # From iFogSim SENSOR_TRANSMISSION_TIME
    }

# Simulate edge biometric processing (biometricModule)
def process_biometric_data(raw_data):
    """Simulate biometric data processing at edge device - matches iFogSim biometricModule"""
    processed = {
        "device_id": DEVICE_ID,
        "application_id": "precision-agriculture-monitoring",
        "processed_at": "edge-device",
        "processing_delay_ms": 3.0,  # From iFogSim results - GYROSCOPE/ACCELEROMETER processing time
        **raw_data
    }
    
    # Add biometric processing logic matching iFogSim
    processed["gyroscope_analysis"] = {
        "stability_score": round(random.uniform(0.5, 1.0), 3),
        "motion_detected": abs(raw_data["GYROSCOPE"]["angular_velocity"]) > 5.0
    }
    
    processed["accelerometer_analysis"] = {
        "impact_detected": raw_data["ACCELEROMETER"]["magnitude"] > 15.0,
        "activity_level": "high" if raw_data["ACCELEROMETER"]["magnitude"] > 10.0 else "normal"
    }
    
    processed["proximity_analysis"] = {
        "object_nearby": raw_data["PROXIMITY"]["distance"] < 50.0,
        "alert_level": "critical" if raw_data["PROXIMITY"]["distance"] < 10.0 else "normal"
    }
    
    # Generate _BIOMETRIC_TO_ANALYSIS_ tuple for fog processing
    processed["biometric_to_analysis_tuple"] = {
        "tuple_cpu_delay": 0.41249999999990905,  # From iFogSim results
        "data_size": 2500,  # bytes - from Java code
        "network_delay": 1800  # ms - from Java code
    }
    
    return processed

# Simulate fog-level health analysis (healthAnalysisModule)
def analyze_health_data(biometric_data):
    """Simulate health analysis at fog node level - matches iFogSim healthAnalysisModule"""
    health_issues = []
    alert_level = "normal"
    
    # Gyroscope-based analysis
    if biometric_data["gyroscope_analysis"]["motion_detected"]:
        health_issues.append("EXCESSIVE_MOVEMENT")
        alert_level = "medium"
    
    # Accelerometer-based analysis  
    if biometric_data["accelerometer_analysis"]["impact_detected"]:
        health_issues.append("IMPACT_DETECTED")
        alert_level = "high"
    
    # Proximity-based analysis
    if biometric_data["proximity_analysis"]["object_nearby"]:
        health_issues.append("OBSTACLE_DETECTED")
        if biometric_data["proximity_analysis"]["alert_level"] == "critical":
            alert_level = "critical"
    
    # Generate analysis result matching iFogSim loops
    analysis_result = {
        **biometric_data,
        "health_issues": health_issues,
        "issue_count": len(health_issues),
        "alert_level": alert_level,
        "analyzed_at": "fog-node"
    }
    
    # Add specific loop delays from iFogSim results
    if "GYROSCOPE" in str(biometric_data) and alert_level == "critical":
        # Critical health loop: [GYROSCOPE, biometricModule, healthAnalysisModule, cloudModule, EMERGENCY_ALERT]
        analysis_result["loop_delay_ms"] = 34.162499999999966
        analysis_result["loop_type"] = "critical_health_loop"
    else:
        # Routine monitoring loop: [PROXIMITY, biometricModule, healthAnalysisModule, HEALTH_NOTIFICATION]  
        analysis_result["loop_delay_ms"] = 13.651647286821639
        analysis_result["loop_type"] = "routine_monitoring_loop"
    
    # Add _ANALYSIS_TO_CLOUD_ tuple for cloud processing
    analysis_result["analysis_to_cloud_tuple"] = {
        "tuple_cpu_delay": 0.21000000000003638,  # From iFogSim results
        "data_size": 2200,  # bytes - from Java code
        "network_delay": 1600  # ms - from Java code
    }
    
    return analysis_result

# Simulate cloud analysis (cloudModule)
def perform_cloud_analysis(health_analysis_data):
    """Simulate advanced cloud analysis - matches iFogSim cloudModule"""
    cloud_confidence = random.uniform(0.8, 0.99)
    
    # Advanced pattern analysis based on iFogSim architecture
    patterns = []
    if health_analysis_data["issue_count"] > 1:
        patterns.append("MULTI_SENSOR_CORRELATION")
    
    if "IMPACT_DETECTED" in health_analysis_data["health_issues"]:
        patterns.append("PHYSICAL_IMPACT_PATTERN")
    
    if "EXCESSIVE_MOVEMENT" in health_analysis_data["health_issues"] and "OBSTACLE_DETECTED" in health_analysis_data["health_issues"]:
        patterns.append("COLLISION_RISK_PATTERN")
    
    # Actions based on alert level and patterns - matching iFogSim actuators
    recommended_actions = []
    if health_analysis_data["alert_level"] == "critical":
        recommended_actions.append("EMERGENCY_ALERT")  # Matches EMERGENCY_ALERT actuator
    elif health_analysis_data["alert_level"] in ["high", "medium"]:
        recommended_actions.append("HEALTH_NOTIFICATION")  # Matches HEALTH_NOTIFICATION actuator
    else:
        recommended_actions.append("ROUTINE_MONITORING")
    
    cloud_result = {
        **health_analysis_data,
        "cloud_patterns": patterns,
        "cloud_confidence": cloud_confidence,
        "recommended_actions": recommended_actions,
        "cloud_analysis_at": "cloud",
        "execution_time_ms": 232  # From iFogSim EXECUTION TIME results
    }
    
    # Add energy consumption data from iFogSim results
    cloud_result["energy_consumption"] = {
        "cloud_energy": 3701548.874999916,
        "fog_node_energy": 240755.0000000157,
        "edge_device_energy": 239058.5,
        "execution_cost": 81239.10000010965,
        "total_network_usage": 21258.8
    }
    
    return cloud_result

# ========= AWS IoT Integration Functions =========

def publish_to_aws_iot(topic, payload):
    """Publish data to AWS IoT Core"""
    if not iot_client:
        print(f"⚠️  IoT client not initialized. Would publish to {topic}")
        return False
    
    try:
        response = iot_client.publish(
            topic=topic,
            qos=1,
            payload=json.dumps(payload, indent=2)
        )
        return True
    except Exception as e:
        print(f"❌ Error publishing to AWS IoT: {e}")
        return False

def send_device_shadow_update(state):
    """Update AWS IoT Device Shadow"""
    if not iot_client:
        print(f"⚠️  IoT client not initialized. Would update shadow with: {state}")
        return False
        
    try:
        shadow_payload = {
            "state": {
                "reported": state
            }
        }
        
        response = iot_client.update_thing_shadow(
            thingName=THING_NAME,
            payload=json.dumps(shadow_payload)
        )
        print(f"🔄 Device shadow updated successfully")
        return True
    except Exception as e:
        print(f"❌ Error updating device shadow: {e}")
        return False

def simulate_actuator_responses(cloud_result):
    """Simulate actuator responses based on cloud analysis - matches iFogSim actuators"""
    responses = []
    
    for action in cloud_result["recommended_actions"]:
        if action == "EMERGENCY_ALERT":
            responses.append({
                "actuator": "a-emergency-alert",
                "action": "EMERGENCY_ALERT",
                "status": "executed",
                "latency_ms": 0.5,  # From iFogSim Java code
                "gateway_device": "edge-device",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif action == "HEALTH_NOTIFICATION":
            responses.append({
                "actuator": "a-health-notification", 
                "action": "HEALTH_NOTIFICATION",
                "status": "executed",
                "latency_ms": 0.8,  # From iFogSim Java code
                "gateway_device": "edge-device",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif action == "ROUTINE_MONITORING":
            responses.append({
                "actuator": "a-routine-monitor",
                "action": "ROUTINE_MONITORING",
                "status": "executed", 
                "latency_ms": 0.3,
                "gateway_device": "edge-device",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    return responses

def run_precision_agriculture_simulation():
    """Main simulation loop matching iFogSim precision agriculture architecture"""
    print("🚀 Starting AWS IoT Precision Agriculture Simulation...")
    print(f"📡 Connected to AWS IoT Endpoint: {AWS_IOT_ENDPOINT}")
    print(f"🔧 Device: {DEVICE_ID} | Thing: {THING_NAME}")
    print("=" * 60)
    
    simulation_count = 0
    
    try:
        while True:
            simulation_count += 1
            print(f"\n🔄 Simulation Cycle #{simulation_count}")
            print("-" * 40)
            
            # Step 1: Generate raw sensor data (matching iFogSim sensors)
            raw_sensor_data = generate_precision_agriculture_sensor_data()
            print(f"📊 Raw Sensor Data: GYROSCOPE, ACCELEROMETER, PROXIMITY")
            
            # Step 2: Edge biometric processing (biometricModule)
            biometric_data = process_biometric_data(raw_sensor_data)
            print(f"🔧 Biometric Processing Complete (Edge Device)")
            
            # Publish biometric data
            publish_to_aws_iot(TOPICS["biometric_data"], biometric_data)
            
            # Step 3: Fog health analysis (healthAnalysisModule)
            health_analysis = analyze_health_data(biometric_data)
            print(f"🏥 Health Analysis: {health_analysis['issue_count']} issues, Level: {health_analysis['alert_level']}")
            print(f"⏱️  Loop: {health_analysis['loop_type']} (Delay: {health_analysis['loop_delay_ms']:.2f}ms)")
            
            # Publish health analysis
            publish_to_aws_iot(TOPICS["health_analysis"], health_analysis)
            
            # Step 4: Cloud analysis (cloudModule)
            cloud_result = perform_cloud_analysis(health_analysis)
            print(f"☁️  Cloud Analysis: Confidence {cloud_result['cloud_confidence']:.2f}, Actions: {cloud_result['recommended_actions']}")
            
            # Publish cloud results
            publish_to_aws_iot(TOPICS["cloud_analysis"], cloud_result)
            
            # Step 5: Actuator responses
            actuator_responses = simulate_actuator_responses(cloud_result)
            for response in actuator_responses:
                print(f"⚡ Actuator Response: {response['actuator']} -> {response['action']} (Latency: {response['latency_ms']}ms)")
                
                # Publish to appropriate actuator topic
                if response['action'] == 'EMERGENCY_ALERT':
                    publish_to_aws_iot(TOPICS["emergency_alerts"], response)
                elif response['action'] == 'HEALTH_NOTIFICATION':
                    publish_to_aws_iot(TOPICS["health_notifications"], response)
            
            # Step 6: Update device shadow with current state
            device_state = {
                "sensor_readings": {
                    "gyroscope_angular_velocity": raw_sensor_data["GYROSCOPE"]["angular_velocity"],
                    "accelerometer_magnitude": raw_sensor_data["ACCELEROMETER"]["magnitude"],
                    "proximity_distance": raw_sensor_data["PROXIMITY"]["distance"]
                },
                "health_analysis": {
                    "issues_detected": health_analysis["issue_count"],
                    "alert_level": health_analysis["alert_level"],
                    "loop_type": health_analysis["loop_type"]
                },
                "performance": {
                    "execution_time_ms": cloud_result["execution_time_ms"],
                    "cloud_confidence": cloud_result["cloud_confidence"]
                },
                "last_update": datetime.utcnow().isoformat(),
                "simulation_cycle": simulation_count
            }
            send_device_shadow_update(device_state)
            
            # Simulate the actual execution delay from iFogSim results
            gyroscope_delay = 3.0  # From iFogSim TUPLE CPU EXECUTION DELAY
            accelerometer_delay = 3.0  # From iFogSim results
            proximity_delay = 1.4500000000000455  # From iFogSim results
            biometric_to_analysis_delay = 0.41249999999990905  # From iFogSim results
            analysis_to_cloud_delay = 0.21000000000003638  # From iFogSim results
            
            total_delay = (gyroscope_delay + accelerometer_delay + proximity_delay + 
                          biometric_to_analysis_delay + analysis_to_cloud_delay) / 1000.0
            
            print(f"⏱️  Total Processing Delay: {total_delay:.3f}s")
            print(f"🔋 Energy - Cloud: {cloud_result['energy_consumption']['cloud_energy']:.0f}, Fog: {cloud_result['energy_consumption']['fog_node_energy']:.0f}")
            print("✅ Simulation cycle completed")
            
            # Wait before next cycle (matching SENSOR_TRANSMISSION_TIME from Java)
            time.sleep(3.0)  # 3.0 seconds from iFogSim SENSOR_TRANSMISSION_TIME
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted by user")
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
    finally:
        print("🔌 Precision Agriculture Simulation terminated")

# ========= AWS Setup Functions =========

def setup_aws_iot_resources():
    """Set up AWS IoT resources if they don't exist"""
    try:
        # Check if thing exists
        boto3.client('iot').describe_thing(thingName=THING_NAME)
        print(f"✅ Thing '{THING_NAME}' already exists")
    except:
        try:
            # Create thing
            boto3.client('iot').create_thing(thingName=THING_NAME)
            print(f"✅ Created thing '{THING_NAME}'")
        except Exception as e:
            print(f"⚠️  Could not create thing: {e}")

def test_aws_iot_connection():
    """Test AWS IoT connection and publish a test message"""
    if not iot_client:
        print("❌ Cannot test connection - IoT client not initialized")
        return False
    
    try:
        test_payload = {
            "message": "Test connection from Precision Agriculture Simulation",
            "timestamp": datetime.utcnow().isoformat(),
            "device": DEVICE_ID,
            "thing": THING_NAME,
            "simulation_type": "precision-agriculture-monitoring",
            "endpoint": AWS_IOT_ENDPOINT
        }
        
        # Test publishing to each configured topic
        for topic_name, topic_path in TOPICS.items():
            response = iot_client.publish(
                topic=f"{topic_path}/test",
                qos=1,
                payload=json.dumps(test_payload)
            )
            print(f"✅ Test message sent to {topic_name}: {topic_path}/test")
        
        return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def print_simulation_info():
    """Print simulation information"""
    print("""
� Precision Agriculture IoT Simulation  
===============================================
Based on iFogSim Java implementation with AWS IoT integration

📊 Sensors: GYROSCOPE, ACCELEROMETER, PROXIMITY
🔧 Edge Processing: biometricModule  
🏥 Fog Analysis: healthAnalysisModule
☁️  Cloud Processing: cloudModule
⚡ Actuators: EMERGENCY_ALERT, HEALTH_NOTIFICATION

📈 Expected delays (from iFogSim results):
- Critical health loop: 34.16ms (GYROSCOPE → EMERGENCY_ALERT)
- Routine monitoring loop: 13.65ms (PROXIMITY → HEALTH_NOTIFICATION)  
- Sensor transmission time: 3.0s

🔋 Energy consumption (from iFogSim):
- Cloud: 3,701,549 units
- Fog Node: 240,755 units  
- Edge Device: 239,059 units

🌐 AWS IoT Topics:
- agriculture/edge/{device}/biometric
- agriculture/fog/{device}/health-analysis
- agriculture/cloud/{device}/cloud-analysis
- agriculture/actuators/{device}/emergency
- agriculture/actuators/{device}/notifications
""")

# ========= Main Execution =========

if __name__ == "__main__":
    print("🚀 Starting Precision Agriculture AWS IoT Simulation...")
    print(f"📡 Endpoint: {AWS_IOT_ENDPOINT}")
    print(f"🔧 Thing: {THING_NAME}")
    print(f"🆔 Client: {DEVICE_ID}")
    print(f"📋 Topics loaded: {len(TOPICS)} topics")
    
    if AWS_IOT_ENDPOINT:
        print_simulation_info()
        setup_aws_iot_resources()
        
        # Test connection before starting simulation
        print("\n🔍 Testing AWS IoT connection...")
        if test_aws_iot_connection():
            print("✅ Connection test successful!")
            print("\n🎬 Starting precision agriculture simulation in 3 seconds...")
            time.sleep(3)
            run_precision_agriculture_simulation()
        else:
            print("❌ Connection test failed. Please check your AWS IoT setup.")
    else:
        print(f"""
❌ Could not get AWS IoT endpoint. 

📋 Current configuration status:
- Config file loaded: {'Yes' if AWS_CONFIG else 'No'}
- Endpoint available: {'No' if not AWS_IOT_ENDPOINT else 'Yes'}

Please ensure:
1. aws-iot-config.json exists with proper configuration
2. AWS CLI is installed and configured: aws configure
3. You have proper AWS IoT permissions

💡 Quick setup commands:
aws iot create-thing --thing-name AgricultureEdgeDevice
aws iot create-policy --policy-name PrecisionAgriculturePolicy --policy-document '{
  "Version": "2012-10-17",
  "Statement": [{{"Effect": "Allow", "Action": "iot:*", "Resource": "*"}}]
}'
""")
