<template>
  <div class="role-shell">
    <el-alert
      title="管理员视角：可跨班迁移小组并批量修正成员角色"
      type="error"
      :closable="false"
      class="role-alert"
    />

    <el-card class="admin-ops" shadow="never">
      <div class="admin-ops-head">
        <strong>系统级操作</strong>
        <div class="op-actions">
          <el-button type="primary" size="small" @click="openMigrateDialog">跨班迁移小组</el-button>
          <el-button type="warning" size="small" @click="openBatchDialog">批量修正成员角色</el-button>
        </div>
      </div>
      <p>管理员操作执行后将自动刷新小组页面数据。</p>
    </el-card>

    <GroupsLegacy :key="legacyKey" />

    <el-dialog v-model="showMigrateDialog" title="跨班迁移小组" width="560px" :close-on-click-modal="false">
      <el-form :model="migrateForm" label-width="110px">
        <el-form-item label="小组">
          <el-select v-model="migrateForm.group_id" filterable placeholder="选择小组" style="width: 100%">
            <el-option
              v-for="group in groups"
              :key="group.id"
              :label="`${group.group_name} (#${group.id})`"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标班级">
          <el-select v-model="migrateForm.target_class_id" filterable placeholder="选择班级" style="width: 100%">
            <el-option v-for="cls in classes" :key="cls.id" :label="cls.class_name" :value="cls.id" />
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

    <el-dialog v-model="showBatchDialog" title="批量修正成员角色" width="680px" :close-on-click-modal="false">
      <el-form label-width="110px" class="batch-form">
        <el-form-item label="选择小组">
          <el-select v-model="batchGroupId" filterable placeholder="选择小组" style="width: 100%" @change="loadGroupMembers">
            <el-option
              v-for="group in groups"
              :key="group.id"
              :label="`${group.group_name} (#${group.id})`"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <el-table :data="batchMembers" size="small" v-loading="batchLoading">
        <el-table-column prop="student_name" label="姓名" width="140" />
        <el-table-column prop="username" label="用户名" width="160" />
        <el-table-column label="角色">
          <template #default="{ row }">
            <el-select v-model="row.role" style="width: 100%">
              <el-option label="组长" value="leader" />
              <el-option label="记录员" value="recorder" />
              <el-option label="操作员" value="operator" />
              <el-option label="汇报员" value="reporter" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitBatchRoles">批量提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import GroupsLegacy from '../Groups.vue';
import { getGroups, getGroupDetail, migrateGroup, batchUpdateGroupMemberRoles } from '../../api/groups';
import { getClasses } from '../../api/classes';
import { getDevices } from '../../api/devices';
import { getErrorMessage } from '../../utils/error';

const legacyKey = ref(0);
const showMigrateDialog = ref(false);
const showBatchDialog = ref(false);
const submitting = ref(false);
const batchLoading = ref(false);

const groups = ref<any[]>([]);
const classes = ref<any[]>([]);
const devices = ref<any[]>([]);
const batchMembers = ref<any[]>([]);

const migrateForm = ref({
  group_id: undefined as number | undefined,
  target_class_id: undefined as number | undefined,
  target_device_id: undefined as number | undefined,
});

const batchGroupId = ref<number | undefined>(undefined);

const loadBaseOptions = async () => {
  const [groupList, classList, deviceList] = await Promise.all([
    getGroups(),
    getClasses(),
    getDevices(),
  ]);
  groups.value = groupList;
  classes.value = classList;
  devices.value = deviceList;
};

const openMigrateDialog = async () => {
  try {
    await loadBaseOptions();
    showMigrateDialog.value = true;
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '加载迁移数据失败'));
  }
};

const submitMigrate = async () => {
  if (!migrateForm.value.group_id || !migrateForm.value.target_class_id) {
    ElMessage.warning('请选择小组与目标班级');
    return;
  }

  submitting.value = true;
  try {
    await migrateGroup(migrateForm.value.group_id, {
      target_class_id: migrateForm.value.target_class_id,
      target_device_id: migrateForm.value.target_device_id ?? null,
    });
    ElMessage.success('小组迁移成功');
    showMigrateDialog.value = false;
    legacyKey.value += 1;
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '小组迁移失败'));
  } finally {
    submitting.value = false;
  }
};

const openBatchDialog = async () => {
  try {
    await loadBaseOptions();
    batchGroupId.value = undefined;
    batchMembers.value = [];
    showBatchDialog.value = true;
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '加载批量修正数据失败'));
  }
};

const loadGroupMembers = async () => {
  if (!batchGroupId.value) {
    batchMembers.value = [];
    return;
  }

  batchLoading.value = true;
  try {
    const detail = await getGroupDetail(batchGroupId.value);
    batchMembers.value = (detail.members || []).map((item: any) => ({ ...item }));
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '加载小组成员失败'));
  } finally {
    batchLoading.value = false;
  }
};

const submitBatchRoles = async () => {
  if (!batchGroupId.value) {
    ElMessage.warning('请先选择小组');
    return;
  }

  const updates = batchMembers.value.map((item: any) => ({
    member_id: item.id,
    role: item.role,
  }));

  submitting.value = true;
  try {
    await batchUpdateGroupMemberRoles(batchGroupId.value, updates);
    ElMessage.success('批量角色修正成功');
    showBatchDialog.value = false;
    legacyKey.value += 1;
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '批量角色修正失败'));
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
  gap: 12px;
}

.op-actions {
  display: flex;
  gap: 8px;
}

.admin-ops p {
  margin: 8px 0 0;
  color: #666;
}

.batch-form {
  margin-bottom: 12px;
}
</style>
