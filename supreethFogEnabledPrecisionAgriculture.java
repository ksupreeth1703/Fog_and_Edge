package org.fog.test.perfeval;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.LinkedList;
import java.util.List;

import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Storage;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.power.PowerHost;
import org.cloudbus.cloudsim.provisioners.RamProvisionerSimple;
import org.cloudbus.cloudsim.sdn.overbooking.BwProvisionerOverbooking;
import org.cloudbus.cloudsim.sdn.overbooking.PeProvisionerOverbooking;
import org.fog.application.AppEdge;
import org.fog.application.AppLoop;
import org.fog.application.Application;
import org.fog.application.selectivity.FractionalSelectivity;
import org.fog.entities.Actuator;
import org.fog.entities.FogBroker;
import org.fog.entities.FogDevice;
import org.fog.entities.FogDeviceCharacteristics;
import org.fog.entities.Sensor;
import org.fog.entities.Tuple;
import org.fog.placement.Controller;
import org.fog.placement.ModuleMapping;
import org.fog.placement.ModulePlacementEdgewards;
import org.fog.policy.AppModuleAllocationPolicy;
import org.fog.scheduler.StreamOperatorScheduler;
import org.fog.utils.FogLinearPowerModel;
import org.fog.utils.FogUtils;
import org.fog.utils.TimeKeeper;
import org.fog.utils.distribution.DeterministicDistribution;

public class supreethFogEnabledPrecisionAgriculture {

    static List<FogDevice> fogDevices = new ArrayList<>();
    static List<Sensor> sensors = new ArrayList<>();
    static List<Actuator> actuators = new ArrayList<>();
    static double SENSOR_TRANSMISSION_TIME = 3.0;

    public static void main(String[] args) {
        Log.printLine("Starting Fog-Enabled Precision Agriculture Simulation...");
        try {
            Log.disable();
            int num_user = 1;
            Calendar calendar = Calendar.getInstance();
            boolean trace_flag = false;
            CloudSim.init(num_user, calendar, trace_flag);

            String appId = "precision-agriculture-monitoring";
            FogBroker broker = new FogBroker("broker");
            Application application = createApplication(appId, broker.getId());
            application.setUserId(broker.getId());

            createFogDevices(broker.getId(), appId);

            Controller controller = new Controller("master-controller", fogDevices, sensors, actuators);
            ModuleMapping moduleMapping = ModuleMapping.createModuleMapping();
            moduleMapping.addModuleToDevice("biometricModule", "edge-device");
            moduleMapping.addModuleToDevice("healthAnalysisModule", "fog-node");
            moduleMapping.addModuleToDevice("cloudModule", "cloud");

            controller.submitApplication(application, new ModulePlacementEdgewards(fogDevices, sensors, actuators, application, moduleMapping));
            TimeKeeper.getInstance().setSimulationStartTime(Calendar.getInstance().getTimeInMillis());

            CloudSim.startSimulation();
            CloudSim.stopSimulation();
            Log.printLine("Fog-Enabled Precision Agriculture Simulation finished!");
        } catch (Exception e) {
            e.printStackTrace();
            Log.printLine("Unwanted errors happened");
        }
    }

    private static void createFogDevices(int userId, String appId) {
        FogDevice cloud = createFogDevice("cloud", 20000, 36000, 20000, 20000, 0, 0.012, 2100.0, 1800.0);
        cloud.setParentId(-1);
        cloud.setUplinkLatency(100);
        fogDevices.add(cloud);

        FogDevice fogNode = createFogDevice("fog-node", 8000, 16000, 4000, 4000, 1, 0.004, 150.0, 100.0);
        fogNode.setParentId(cloud.getId());
        fogNode.setUplinkLatency(10);
        fogDevices.add(fogNode);

        FogDevice edgeDevice = createFogDevice("edge-device", 4000, 8000, 2000, 2000, 2, 0.001, 120.0, 85.0);
        edgeDevice.setParentId(fogNode.getId());
        edgeDevice.setUplinkLatency(4);
        fogDevices.add(edgeDevice);

        addAgricultureSensorsAndActuators(edgeDevice.getId(), userId, appId);
    }

    private static void addAgricultureSensorsAndActuators(int parentId, int userId, String appId) {
        // Sensors updated for Precision Agriculture topic
        sensors.add(new Sensor("s-gyroscope", "GYROSCOPE", userId, appId, new DeterministicDistribution(SENSOR_TRANSMISSION_TIME)));
        sensors.add(new Sensor("s-accelerometer", "ACCELEROMETER", userId, appId, new DeterministicDistribution(SENSOR_TRANSMISSION_TIME)));
        sensors.add(new Sensor("s-proximity", "PROXIMITY", userId, appId, new DeterministicDistribution(SENSOR_TRANSMISSION_TIME)));

        for (Sensor sensor : sensors) {
            sensor.setGatewayDeviceId(parentId);
            sensor.setLatency(0.8);
        }

        // Actuators kept as-is per instruction (logic unchanged)
        Actuator emergencyAlert = new Actuator("a-emergency-alert", userId, appId, "EMERGENCY_ALERT");
        emergencyAlert.setGatewayDeviceId(parentId);
        emergencyAlert.setLatency(0.5);
        actuators.add(emergencyAlert);

        Actuator healthNotification = new Actuator("a-health-notification", userId, appId, "HEALTH_NOTIFICATION");
        healthNotification.setGatewayDeviceId(parentId);
        healthNotification.setLatency(0.8);
        actuators.add(healthNotification);
    }

    private static FogDevice createFogDevice(String nodeName, long mips, int ram, long upBw, long downBw,
                                             int level, double ratePerMips, double busyPower, double idlePower) {
        List<Pe> peList = new ArrayList<>();
        peList.add(new Pe(0, new PeProvisionerOverbooking(mips)));

        int hostId = FogUtils.generateEntityId();
        long storage = 750000;
        int bw = 15000;

        PowerHost host = new PowerHost(
                hostId,
                new RamProvisionerSimple(ram),
                new BwProvisionerOverbooking(bw),
                storage,
                peList,
                new StreamOperatorScheduler(peList),
                new FogLinearPowerModel(busyPower, idlePower)
        );

        List<Host> hostList = new ArrayList<>();
        hostList.add(host);

        FogDeviceCharacteristics characteristics = new FogDeviceCharacteristics(
                "x86", "Linux", "Xen", host, 10.0, 3.0, 0.05, 0.001, 0.0);

        FogDevice device = null;
        try {
            device = new FogDevice(nodeName, characteristics,
                    new AppModuleAllocationPolicy(hostList), new LinkedList<Storage>(), 10, upBw, downBw, 0, ratePerMips);
        } catch (Exception e) {
            e.printStackTrace();
        }

        device.setLevel(level);
        return device;
    }

    private static Application createApplication(String appId, int userId) {
        Application application = Application.createApplication(appId, userId);

        application.addAppModule("biometricModule", 10);
        application.addAppModule("healthAnalysisModule", 16);
        application.addAppModule("cloudModule", 22);

        // Sensor edges updated to agriculture sensors
        application.addAppEdge("GYROSCOPE", "biometricModule", 2000, 1000, "GYROSCOPE", Tuple.UP, AppEdge.SENSOR);
        application.addAppEdge("ACCELEROMETER", "biometricModule", 2200, 1100, "ACCELEROMETER", Tuple.UP, AppEdge.SENSOR);
        application.addAppEdge("PROXIMITY", "biometricModule", 1800, 900, "PROXIMITY", Tuple.UP, AppEdge.SENSOR);

        // Module to module edges (unchanged logic)
        application.addAppEdge("biometricModule", "healthAnalysisModule", 2500, 1800, "_BIOMETRIC_TO_ANALYSIS_", Tuple.UP, AppEdge.MODULE);
        application.addAppEdge("healthAnalysisModule", "cloudModule", 2200, 1600, "_ANALYSIS_TO_CLOUD_", Tuple.UP, AppEdge.MODULE);

        // Actuator edges (unchanged)
        application.addAppEdge("cloudModule", "EMERGENCY_ALERT", 1200, 800, "EMERGENCY_ALERT", Tuple.DOWN, AppEdge.ACTUATOR);
        application.addAppEdge("healthAnalysisModule", "HEALTH_NOTIFICATION", 1000, 600, "HEALTH_NOTIFICATION", Tuple.DOWN, AppEdge.ACTUATOR);

        // Tuple mappings updated to new sensors
        for (String sensor : new String[]{"GYROSCOPE", "ACCELEROMETER", "PROXIMITY"}) {
            application.addTupleMapping("biometricModule", sensor, "_BIOMETRIC_TO_ANALYSIS_", new FractionalSelectivity(1.0));
        }
        application.addTupleMapping("healthAnalysisModule", "_BIOMETRIC_TO_ANALYSIS_", "_ANALYSIS_TO_CLOUD_", new FractionalSelectivity(0.8));
        application.addTupleMapping("healthAnalysisModule", "_BIOMETRIC_TO_ANALYSIS_", "HEALTH_NOTIFICATION", new FractionalSelectivity(0.3));
        application.addTupleMapping("cloudModule", "_ANALYSIS_TO_CLOUD_", "EMERGENCY_ALERT", new FractionalSelectivity(0.1));

        // Application loops adjusted to new sensors (logic structure unchanged)
        final AppLoop criticalHealthLoop = new AppLoop(new ArrayList<String>() {{
            add("GYROSCOPE");
            add("biometricModule");
            add("healthAnalysisModule");
            add("cloudModule");
            add("EMERGENCY_ALERT");
        }});

        final AppLoop routineMonitoringLoop = new AppLoop(new ArrayList<String>() {{
            add("PROXIMITY");
            add("biometricModule");
            add("healthAnalysisModule");
            add("HEALTH_NOTIFICATION");
        }});

        List<AppLoop> loops = new ArrayList<AppLoop>() {{
            add(criticalHealthLoop);
            add(routineMonitoringLoop);
        }};
        application.setLoops(loops);

        return application;
    }
}
