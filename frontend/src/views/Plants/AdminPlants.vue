<template>
  <div class="role-shell">
    <el-alert
      title="管理员视角：可执行跨班迁移与全局治理"
      type="error"
      :closable="false"
      class="role-alert"
    />

    <el-card class="admin-ops" shadow="never">
      <div class="admin-ops-head">
        <strong>系统级操作</strong>
        <el-button type="primary" size="small" @click="openMigrateDialog">跨班迁移植物档案</el-button>
      </div>
      <p>迁移后将自动刷新页面列表，方便现场核验。</p>
    </el-card>

    <PlantsLegacy :key="legacyKey" />

    <el-dialog v-model="showMigrateDialog" title="跨班迁移植物档案" width="560px" :close-on-click-modal="false">
      <el-form :model="migrateForm" label-width="110px">
        <el-form-item label="植物档案">
          <el-select v-model="migrateForm.plant_id" filterable placeholder="选择植物档案" style="width: 100%">
            <el-option
              v-for="plant in plants"
              :key="plant.id"
              :label="`${plant.plant_name} (#${plant.id})`"
              :value="plant.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标班级">
          <el-select v-model="migrateForm.target_class_id" filterable placeholder="选择目标班级" style="width: 100%">
            <el-option v-for="cls in classes" :key="cls.id" :label="cls.class_name" :value="cls.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标小组">
          <el-select v-model="migrateForm.target_group_id" clearable filterable placeholder="可选" style="width: 100%">
            <el-option v-for="group in filteredGroups" :key="group.id" :label="group.group_name" :value="group.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标设备">
          <el-select v-model="migrateForm.target_device_id" clearable filterable placeholder="可选" style="width: 100%">
            <el-option v-for="device in devices" :key="device.id" :label="device.device_name" :value="device.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMigrateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitMigrate">确认迁移</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';
import PlantsLegacy from '../Plants.vue';
import { getPlants, migratePlant } from '../../api/plants';
import { getClasses } from '../../api/classes';
import { getGroups } from '../../api/groups';
import { getDevices } from '../../api/devices';
import { getErrorMessage } from '../../utils/error';

const legacyKey = ref(0);
const showMigrateDialog = ref(false);
const submitting = ref(false);

const plants = ref<any[]>([]);
const classes = ref<any[]>([]);
const groups = ref<any[]>([]);
const devices = ref<any[]>([]);

const migrateForm = ref({
  plant_id: undefined as number | undefined,
  target_class_id: undefined as number | undefined,
  target_group_id: undefined as number | undefined,
  target_device_id: undefined as number | undefined,
});

const filteredGroups = computed(() => {
  if (!migrateForm.value.target_class_id) return groups.value;
  return groups.value.filter((item: any) => item.class_id === migrateForm.value.target_class_id);
});

const loadMigrateOptions = async () => {
  const [plantList, classList, groupList, deviceList] = await Promise.all([
    getPlants(),
    getClasses(),
    getGroups(),
    getDevices(),
  ]);
  plants.value = plantList;
  classes.value = classList;
  groups.value = groupList;
  devices.value = deviceList;
};

const openMigrateDialog = async () => {
  try {
    await loadMigrateOptions();
    showMigrateDialog.value = true;
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '加载迁移数据失败'));
  }
};

const submitMigrate = async () => {
  if (!migrateForm.value.plant_id || !migrateForm.value.target_class_id) {
    ElMessage.warning('请选择植物档案与目标班级');
    return;
  }

  submitting.value = true;
  try {
    await migratePlant(migrateForm.value.plant_id, {
      target_class_id: migrateForm.value.target_class_id,
      target_group_id: migrateForm.value.target_group_id ?? null,
      target_device_id: migrateForm.value.target_device_id ?? null,
    });
    ElMessage.success('迁移成功');
    showMigrateDialog.value = false;
    legacyKey.value += 1;
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '迁移失败'));
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
.role-alert {
  margin: 12px 20px;
}

.admin-ops {
  margin: 0 20px 12px;
}

.admin-ops-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.admin-ops p {
  margin: 8px 0 0;
  color: #666;
}
</style>
