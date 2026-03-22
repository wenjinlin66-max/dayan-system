<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,#ecf6ff_0%,#f8fbff_42%,#eef2f7_100%)] p-6 text-slate-900">
    <WorkspaceTopNav
      title="业务表格区"
      description="产品主表 → 产品 BOM → 客户订单 → 零件需求/部门分发表的最小闭环演示区。"
    />

    <div class="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)_360px]">
      <aside class="rounded-[28px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_22px_60px_rgba(15,23,42,0.08)]">
        <div class="text-[11px] uppercase tracking-[0.24em] text-cyan-700/75">Tables</div>
        <div class="mt-3 rounded-[20px] border border-cyan-100 bg-cyan-50/80 px-3 py-3 text-xs leading-6 text-cyan-900/80">
          先维护产品和 BOM，再录入客户订单。订单会自动拆成零件需求，并下发到采购/生产/客户配合三张表。
        </div>

        <div class="mt-4 space-y-2">
          <button
            v-for="table in tables"
            :key="table.table_name"
            class="w-full rounded-[22px] border px-4 py-3 text-left transition"
            :class="table.table_name === currentTable ? 'border-cyan-300 bg-cyan-50 shadow-sm shadow-cyan-100' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'"
            @click="selectTable(table.table_name)"
          >
            <div class="text-sm font-semibold text-slate-900">{{ table.label }}</div>
            <div class="mt-1 text-xs leading-5 text-slate-500">{{ table.description }}</div>
          </button>
        </div>
      </aside>

      <section class="rounded-[30px] border border-slate-200/80 bg-white/94 p-5 shadow-[0_30px_80px_rgba(15,23,42,0.10)]">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div class="text-[11px] uppercase tracking-[0.24em] text-slate-500">Table Workbench</div>
            <div class="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{{ currentTableMeta?.label || '选择业务表' }}</div>
            <div class="mt-1 text-sm text-slate-500">{{ currentTable }}</div>
          </div>
          <div class="flex flex-wrap gap-3">
            <el-button @click="refreshAll">刷新</el-button>
            <el-button v-if="isProductWorkspace" :disabled="!selectedProduct" @click="openCreateDialog('product_bom')">新增 BOM</el-button>
            <el-button type="primary" :disabled="!canCreateCurrentTable" @click="openCreateDialog(currentTable)">
              {{ currentCreateLabel }}
            </el-button>
          </div>
        </div>

        <div class="mt-4 flex flex-wrap items-center gap-2">
          <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-500">
            {{ currentRowCount }} 条记录
          </span>
          <span v-if="selectedProduct" class="rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-xs text-cyan-700">
            当前产品：{{ String(selectedProduct.product_name || selectedProduct.product_code || '') }}
          </span>
          <span v-if="selectedOrder" class="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs text-violet-700">
            当前订单：{{ String(selectedOrder.order_no || '') }}
          </span>
          <span v-if="lastMutationSummary" class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs text-emerald-700">
            {{ lastMutationSummary }}
          </span>
        </div>

        <div v-if="isProductWorkspace" class="mt-5 grid gap-4 xl:grid-cols-[340px_minmax(0,1fr)]">
          <section class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-4">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">Product Master</div>
                <div class="mt-1 text-lg font-semibold text-slate-900">产品主表</div>
              </div>
              <el-button type="primary" plain @click="openCreateDialog('product_master')">新增产品</el-button>
            </div>

            <el-table
              v-loading="loading"
              :data="productRows"
              class="mt-4"
              stripe
              border
              height="620"
              @row-click="handleProductRowClick"
            >
              <el-table-column prop="product_code" label="产品编码" min-width="130" />
              <el-table-column prop="product_name" label="产品名称" min-width="180" />
              <el-table-column prop="unit_price" label="标准售价" min-width="120">
                <template #default="scope">{{ formatCurrency(scope.row.unit_price) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="scope">
                  <div class="flex gap-2">
                    <el-button size="small" @click.stop="openEditDialog('product_master', scope.row)">编辑</el-button>
                    <el-button size="small" type="danger" plain @click.stop="removeRow('product_master', scope.row)">删除</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

          </section>

          <section class="space-y-4">
            <div v-if="selectedProduct" class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-4">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">Product Detail</div>
                  <div class="mt-1 text-lg font-semibold text-slate-900">当前产品详情</div>
                </div>
                <el-button @click="openEditDialog('product_master', selectedProduct)">编辑当前产品</el-button>
              </div>

              <div class="mt-4 rounded-[22px] border border-slate-200 bg-white p-4">
                <div class="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div class="text-xl font-semibold text-slate-950">{{ String(selectedProduct.product_name || '') }}</div>
                    <div class="mt-1 text-sm text-slate-500">{{ String(selectedProduct.product_code || '-') }} · {{ String(selectedProduct.product_version || '-') }}</div>
                  </div>
                  <span class="rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-xs text-cyan-700">
                    {{ String(selectedProduct.category || '未分类') }}
                  </span>
                </div>
                <div class="mt-4 grid gap-3 sm:grid-cols-3">
                  <div class="rounded-2xl bg-slate-50 px-4 py-3">
                    <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">标准售价</div>
                    <div class="mt-2 text-sm font-medium text-slate-900">{{ formatCurrency(selectedProduct.unit_price) }}</div>
                  </div>
                  <div class="rounded-2xl bg-slate-50 px-4 py-3">
                    <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">BOM 条数</div>
                    <div class="mt-2 text-sm font-medium text-slate-900">{{ selectedProductBomRows.length }} 项</div>
                  </div>
                  <div class="rounded-2xl bg-slate-50 px-4 py-3">
                    <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">维护方式</div>
                    <div class="mt-2 text-sm font-medium text-slate-900">在当前产品页内直接维护 BOM</div>
                  </div>
                </div>
                <div class="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
                  {{ String(selectedProduct.customer_notes || '暂无补充说明') }}
                </div>
              </div>
            </div>

            <section class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-4">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">Product BOM</div>
                  <div class="mt-1 text-lg font-semibold text-slate-900">当前产品 BOM</div>
                  <div class="mt-1 text-sm text-slate-500">BOM 作为所选产品的嵌套维护区，不单独脱离产品详情。</div>
                </div>
                <div class="flex items-center gap-3">
                  <div class="text-sm text-slate-500">{{ selectedProductBomRows.length }} 条组成项</div>
                  <el-button type="primary" plain :disabled="!selectedProduct" @click="openCreateDialog('product_bom')">为当前产品新增 BOM</el-button>
                </div>
              </div>

              <div v-if="!selectedProduct" class="mt-4 rounded-[22px] border border-dashed border-slate-200 bg-white px-4 py-10 text-center text-sm text-slate-500">
                先在左侧选中一个产品，再在这里维护这个产品的零件组成。
              </div>

              <el-table v-else v-loading="loading" :data="selectedProductBomRows" class="mt-4" stripe border height="420">
                <el-table-column prop="part_code" label="零件编码" min-width="120" />
                <el-table-column prop="part_name" label="零件名称" min-width="160" />
                <el-table-column prop="qty_per_unit" label="单件用量" min-width="100" />
                <el-table-column prop="source_type" label="来源类型" min-width="120">
                  <template #default="scope">
                    <span class="rounded-full border px-2.5 py-1 text-[11px]" :class="sourceTypeClass(scope.row.source_type)">
                      {{ sourceTypeLabel(scope.row.source_type) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="unit_cost" label="单件成本" min-width="120">
                  <template #default="scope">{{ formatCurrency(scope.row.unit_cost) }}</template>
                </el-table-column>
                <el-table-column prop="source_ref" label="来源说明" min-width="160" show-overflow-tooltip />
                <el-table-column label="操作" width="150" fixed="right">
                  <template #default="scope">
                    <div class="flex gap-2">
                      <el-button size="small" @click="openEditDialog('product_bom', scope.row)">编辑</el-button>
                      <el-button size="small" type="danger" plain @click="removeRow('product_bom', scope.row)">删除</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </section>
          </section>
        </div>

        <div v-else-if="isOrderWorkspace" class="mt-5 grid gap-4 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
          <section class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-4">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">Customer Orders</div>
                <div class="mt-1 text-lg font-semibold text-slate-900">客户订单</div>
              </div>
              <el-button type="primary" plain @click="openCreateDialog('customer_order')">新增订单</el-button>
            </div>

            <el-table
              v-loading="loading"
              :data="orderRows"
              class="mt-4"
              stripe
              border
              height="560"
              @row-click="handleOrderRowClick"
            >
              <el-table-column prop="order_no" label="订单编号" min-width="150" />
              <el-table-column prop="customer_name" label="客户名称" min-width="120" />
              <el-table-column prop="product_name" label="产品名称" min-width="150" />
              <el-table-column prop="ordered_qty" label="数量" min-width="90" />
              <el-table-column prop="total_amount" label="订单金额" min-width="120">
                <template #default="scope">{{ formatCurrency(scope.row.total_amount) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="scope">
                  <div class="flex gap-2">
                    <el-button size="small" @click.stop="openEditDialog('customer_order', scope.row)">编辑</el-button>
                    <el-button size="small" type="danger" plain @click.stop="removeRow('customer_order', scope.row)">删除</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </section>

          <section class="space-y-4">
            <div class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-4">
              <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">Order Projection</div>
              <div class="mt-1 text-lg font-semibold text-slate-900">订单拆解结果</div>

              <div v-if="selectedOrder" class="mt-4 grid gap-3 sm:grid-cols-3">
                <div class="rounded-2xl bg-white px-4 py-3">
                  <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">订单</div>
                  <div class="mt-2 text-sm font-medium text-slate-900">{{ String(selectedOrder.order_no || '-') }}</div>
                </div>
                <div class="rounded-2xl bg-white px-4 py-3">
                  <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">客户</div>
                  <div class="mt-2 text-sm font-medium text-slate-900">{{ String(selectedOrder.customer_name || '-') }}</div>
                </div>
                <div class="rounded-2xl bg-white px-4 py-3">
                  <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">产品 / 数量</div>
                  <div class="mt-2 text-sm font-medium text-slate-900">{{ String(selectedOrder.product_name || '-') }} × {{ String(selectedOrder.ordered_qty || 0) }}</div>
                </div>
              </div>

              <el-table v-loading="loading" :data="selectedOrderDemandRows" class="mt-4" stripe border height="220">
                <el-table-column prop="part_name" label="零件名称" min-width="150" />
                <el-table-column prop="source_type" label="来源类型" min-width="120">
                  <template #default="scope">
                    <span class="rounded-full border px-2.5 py-1 text-[11px]" :class="sourceTypeClass(scope.row.source_type)">
                      {{ sourceTypeLabel(scope.row.source_type) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="required_qty" label="总需求" min-width="90" />
                <el-table-column prop="purchase_qty" label="采购" min-width="90" />
                <el-table-column prop="manufacture_qty" label="生产" min-width="90" />
                <el-table-column prop="customer_qty" label="客户提供" min-width="100" />
                <el-table-column prop="total_cost" label="总成本" min-width="110">
                  <template #default="scope">{{ formatCurrency(scope.row.total_cost) }}</template>
                </el-table-column>
              </el-table>
            </div>

            <div class="grid gap-4 xl:grid-cols-3">
              <section class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-4">
                <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">Purchase Form</div>
                <div class="mt-1 text-base font-semibold text-slate-900">销售/采购部</div>
                <el-table v-loading="loading" :data="selectedPurchaseRows" class="mt-3" stripe border height="240">
                  <el-table-column prop="part_name" label="零件" min-width="120" />
                  <el-table-column prop="request_qty" label="数量" min-width="80" />
                  <el-table-column prop="request_status" label="状态" min-width="100" />
                </el-table>
              </section>

              <section class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-4">
                <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">Manufacturing Form</div>
                <div class="mt-1 text-base font-semibold text-slate-900">生产部</div>
                <el-table v-loading="loading" :data="selectedManufacturingRows" class="mt-3" stripe border height="240">
                  <el-table-column prop="part_name" label="零件" min-width="120" />
                  <el-table-column prop="request_qty" label="数量" min-width="80" />
                  <el-table-column prop="request_status" label="状态" min-width="100" />
                </el-table>
              </section>

              <section class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-4">
                <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">Customer Supply Form</div>
                <div class="mt-1 text-base font-semibold text-slate-900">客户配合</div>
                <el-table v-loading="loading" :data="selectedCustomerSupplyRows" class="mt-3" stripe border height="240">
                  <el-table-column prop="part_name" label="零件" min-width="120" />
                  <el-table-column prop="request_qty" label="数量" min-width="80" />
                  <el-table-column prop="request_status" label="状态" min-width="100" />
                </el-table>
              </section>
            </div>
          </section>
        </div>

        <div v-else>
          <el-table v-loading="loading" :data="currentRows" class="mt-5" stripe border height="620">
            <el-table-column
              v-for="field in currentVisibleFields"
              :key="field.name"
              :prop="field.name"
              :label="field.label"
              :min-width="field.name.endsWith('_name') ? 160 : 120"
              show-overflow-tooltip
            >
              <template #default="scope">{{ formatCell(field.name, scope.row[field.name]) }}</template>
            </el-table-column>
            <el-table-column label="操作" fixed="right" width="150">
              <template #default="scope">
                <div class="flex gap-2">
                  <el-button size="small" :disabled="!canEditTable(currentTable)" @click="openEditDialog(currentTable, scope.row)">编辑</el-button>
                  <el-button size="small" type="danger" plain :disabled="!canEditTable(currentTable)" @click="removeRow(currentTable, scope.row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>

      <aside class="rounded-[28px] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff_0%,#f7fbff_100%)] p-4 shadow-[0_22px_60px_rgba(15,23,42,0.08)]">
        <div class="flex items-center justify-between gap-3">
          <div class="text-[11px] uppercase tracking-[0.24em] text-violet-700/70">Triggered Workflows</div>
          <div class="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-[11px] text-violet-700">{{ triggeredRecentEvents.length }} 条已触发</div>
        </div>
        <div class="mt-3 max-h-[620px] space-y-3 overflow-y-auto pr-1">
          <div
            v-for="event in triggeredRecentEvents"
            :key="event.change_event_id"
            class="w-full rounded-[22px] border border-slate-200 bg-white/90 p-3 text-left transition hover:border-violet-200 hover:bg-violet-50/40"
          >
            <div class="flex items-center justify-between gap-3">
              <div class="text-sm font-semibold text-slate-900">{{ event.table_name }}</div>
              <span class="rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1 text-[11px] text-violet-700">{{ event.operation }}</span>
            </div>
            <div class="mt-2 text-xs text-slate-500">记录 {{ event.record_id }} · {{ formatEventTime(event.created_at) }}</div>
            <div class="mt-2 text-xs text-emerald-700">触发 execution：{{ event.triggered_execution_ids.join(', ') }}</div>
          </div>
          <div v-if="triggeredRecentEvents.length === 0" class="rounded-[22px] border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-sm text-slate-500">
            暂无已触发 workflow 的最近事件。
          </div>
        </div>
      </aside>
    </div>

    <el-dialog v-model="editorVisible" width="760px" destroy-on-close align-center>
      <template #header>
        <div>
          <div class="text-[11px] uppercase tracking-[0.24em] text-cyan-700/80">Record Editor</div>
          <div class="mt-1 text-xl font-semibold text-slate-900">{{ editorTitle }}</div>
        </div>
      </template>

        <div class="grid gap-4 md:grid-cols-2">
          <div v-for="field in editorFields" :key="field.name">
            <div class="mb-1.5 text-[11px] uppercase tracking-[0.18em] text-slate-500">{{ field.label }}</div>
            <el-select
              v-if="isBomSourceTypeField(field)"
              v-model="draftValues[field.name]"
              class="!w-full"
              @change="handleBomSourceTypeChange"
            >
              <el-option
                v-for="option in BOM_SOURCE_TYPE_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-select
              v-else-if="isBomSourceRefField(field)"
              v-model="draftValues[field.name]"
              class="!w-full"
            >
              <el-option
                v-for="option in bomSourceRefOptionsForDraft"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-input-number
              v-else-if="field.field_type === 'number'"
              v-model="draftValues[field.name]"
              class="!w-full"
              :controls="false"
            />
          <el-input
            v-else-if="field.name.includes('notes')"
            v-model="draftValues[field.name]"
            type="textarea"
            :rows="3"
          />
          <el-input v-else v-model="draftValues[field.name]" />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="editorVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitEditor">保存并触发</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import WorkspaceTopNav from '@/components/layout/WorkspaceTopNav.vue'
import {
  createRecordRow,
  deleteRecordRow,
  fetchRecentRecordEvents,
  fetchRecordRows,
  fetchRecordTableSchema,
  fetchRecordTables,
  updateRecordRow,
} from '@/api/records'
import type {
  RecentRecordEvent,
  RecordsRowListResponse,
  RecordsTableItem,
  RecordsTableSchemaField,
  RecordsTableSchemaResponse,
} from '@/types/records'

const PRODUCT_RELATED_TABLES = ['product_master', 'product_bom'] as const
const ORDER_RELATED_TABLES = ['customer_order', 'parts_demand', 'purchase_request', 'manufacturing_request', 'customer_supply_request'] as const
const BOM_SOURCE_TYPE_OPTIONS = [
  { label: '采购', value: 'purchase' },
  { label: '生产', value: 'manufacture' },
  { label: '客户提供', value: 'customer' },
] as const
const BOM_SOURCE_REF_OPTIONS: Record<string, Array<{ label: string; value: string }>> = {
  purchase: [
    { label: '供应商采购', value: '供应商采购' },
    { label: '现货采购', value: '现货采购' },
    { label: '委外采购', value: '委外采购' },
  ],
  manufacture: [
    { label: '车间生产', value: '车间生产' },
    { label: '自制加工', value: '自制加工' },
    { label: '委托生产', value: '委托生产' },
  ],
  customer: [
    { label: '客户提供', value: '客户提供' },
    { label: '客户寄送', value: '客户寄送' },
    { label: '客户指定供料', value: '客户指定供料' },
  ],
}

const loading = ref(false)
const saving = ref(false)
const editorVisible = ref(false)
const editingMode = ref<'create' | 'edit'>('create')
const editingRecordId = ref('')
const editorTableName = ref('')
const currentTable = ref('')
const selectedProductCode = ref('')
const selectedOrderNo = ref('')
const lastMutationSummary = ref('')
const recentEvents = ref<RecentRecordEvent[]>([])
const tables = ref<RecordsTableItem[]>([])
const tableSchemas = reactive<Record<string, RecordsTableSchemaResponse>>({})
const tableRows = reactive<Record<string, RecordsRowListResponse['rows']>>({})
const draftValues = reactive<Record<string, string | number>>({})

const currentTableMeta = computed(() => tables.value.find((table) => table.table_name === currentTable.value) ?? null)
const currentVisibleFields = computed(() => tableSchemas[currentTable.value]?.fields ?? [])
const currentRows = computed(() => tableRows[currentTable.value] ?? [])
const currentRowCount = computed(() => currentRows.value.length)
const triggeredRecentEvents = computed(() => recentEvents.value.filter((event) => event.triggered_execution_ids.length > 0))
const isProductWorkspace = computed(() => currentTable.value === 'product_master')
const isOrderWorkspace = computed(() => currentTable.value === 'customer_order')
const productRows = computed(() => tableRows.product_master ?? [])
const productBomRows = computed(() => tableRows.product_bom ?? [])
const orderRows = computed(() => tableRows.customer_order ?? [])
const demandRows = computed(() => tableRows.parts_demand ?? [])
const purchaseRows = computed(() => tableRows.purchase_request ?? [])
const manufacturingRows = computed(() => tableRows.manufacturing_request ?? [])
const customerSupplyRows = computed(() => tableRows.customer_supply_request ?? [])
const selectedProduct = computed(() => productRows.value.find((row) => String(row.product_code ?? '') === selectedProductCode.value) ?? null)
const selectedProductBomRows = computed(() => productBomRows.value.filter((row) => String(row.product_code ?? '') === selectedProductCode.value))
const selectedOrder = computed(() => orderRows.value.find((row) => String(row.order_no ?? '') === selectedOrderNo.value) ?? null)
const selectedOrderDemandRows = computed(() => demandRows.value.filter((row) => String(row.order_no ?? '') === selectedOrderNo.value))
const selectedPurchaseRows = computed(() => purchaseRows.value.filter((row) => String(row.order_no ?? '') === selectedOrderNo.value))
const selectedManufacturingRows = computed(() => manufacturingRows.value.filter((row) => String(row.order_no ?? '') === selectedOrderNo.value))
const selectedCustomerSupplyRows = computed(() => customerSupplyRows.value.filter((row) => String(row.order_no ?? '') === selectedOrderNo.value))
const editorFields = computed(() => editableFieldsForTable(editorTableName.value))
const bomSourceRefOptionsForDraft = computed(() => getBomSourceRefOptions(draftValues.source_type))
const canCreateCurrentTable = computed(() => canEditTable(currentTable.value))
const currentCreateLabel = computed(() => {
  if (currentTable.value === 'customer_order') return '新增订单'
  if (currentTable.value === 'product_master') return '新增产品'
  return '新增记录'
})
const editorTitle = computed(() => `${editingMode.value === 'create' ? '新增' : '编辑'} ${tableSchemas[editorTableName.value]?.label || '记录'}`)

const editableFieldsForTable = (tableName: string) => (tableSchemas[tableName]?.fields ?? []).filter((field) => field.editable)
const canEditTable = (tableName: string) => editableFieldsForTable(tableName).length > 0

const formatCurrency = (value: unknown) => {
  const numeric = typeof value === 'number' ? value : Number(value ?? 0)
  return `¥${Number.isFinite(numeric) ? numeric.toLocaleString('zh-CN', { maximumFractionDigits: 2 }) : '0'}`
}

const normalizeBomSourceType = (value: unknown, fallback = 'purchase') => {
  const normalized = String(value ?? '').trim().toLowerCase()
  if (['purchase', '采购', 'buy', 'purchasing', '采购件'].includes(normalized)) return 'purchase'
  if (['manufacture', '生产', '制造', '自制', 'manufacturing'].includes(normalized)) return 'manufacture'
  if (['customer', '客户提供', '客户供料', '客供', '客户', 'customer_supply'].includes(normalized)) return 'customer'
  return fallback
}

const getBomSourceRefOptions = (sourceType: unknown) => BOM_SOURCE_REF_OPTIONS[normalizeBomSourceType(sourceType, 'purchase')] ?? BOM_SOURCE_REF_OPTIONS.purchase

const ensureBomDraftSourceFields = () => {
  if (editorTableName.value !== 'product_bom') return
  const normalizedType = normalizeBomSourceType(draftValues.source_type, 'purchase')
  draftValues.source_type = normalizedType
  const sourceRefOptions = getBomSourceRefOptions(normalizedType)
  const currentSourceRef = typeof draftValues.source_ref === 'string' ? draftValues.source_ref : ''
  if (!sourceRefOptions.some((option) => option.value === currentSourceRef)) {
    draftValues.source_ref = sourceRefOptions[0]?.value ?? ''
  }
}

const handleBomSourceTypeChange = (value: string | number | boolean) => {
  draftValues.source_type = normalizeBomSourceType(value)
  ensureBomDraftSourceFields()
}

const isBomSourceTypeField = (field: RecordsTableSchemaField) => editorTableName.value === 'product_bom' && field.name === 'source_type'

const isBomSourceRefField = (field: RecordsTableSchemaField) => editorTableName.value === 'product_bom' && field.name === 'source_ref'

const sourceTypeLabel = (value: unknown) => {
  const rawSource = String(value ?? '').trim()
  const source = normalizeBomSourceType(value, rawSource)
  if (source === 'purchase') return '采购'
  if (source === 'manufacture') return '生产'
  if (source === 'customer') return '客户提供'
  return source || '-'
}

const sourceTypeClass = (value: unknown) => {
  const source = normalizeBomSourceType(value, String(value ?? '').trim())
  if (source === 'purchase') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (source === 'manufacture') return 'border-amber-200 bg-amber-50 text-amber-700'
  if (source === 'customer') return 'border-violet-200 bg-violet-50 text-violet-700'
  return 'border-slate-200 bg-slate-50 text-slate-600'
}

const formatCell = (fieldName: string, value: unknown) => {
  if (fieldName.includes('cost') || fieldName.includes('price') || fieldName.includes('amount')) {
    return formatCurrency(value)
  }
  if (fieldName === 'source_type') {
    return sourceTypeLabel(value)
  }
  return value == null || value === '' ? '-' : String(value)
}

const formatEventTime = (value?: string | null) => {
  if (!value) return '刚刚'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const normalizeValueForField = (field: RecordsTableSchemaField, value: unknown) => {
  if (field.field_type === 'number') {
    return typeof value === 'number' ? value : Number(value ?? 0)
  }
  return typeof value === 'string' ? value : String(value ?? '')
}

const loadAllTablesData = async () => {
  const tableItems = (await fetchRecordTables()).data.tables
  tables.value = tableItems
  if (!currentTable.value && tableItems[0]) {
    currentTable.value = tableItems[0].table_name
  }

  const allNames = [...new Set(tableItems.map((item) => item.table_name))]
  const payloads = await Promise.all(
    allNames.map(async (tableName) => {
      const [schemaResponse, rowsResponse] = await Promise.all([
        fetchRecordTableSchema(tableName),
        fetchRecordRows(tableName),
      ])
      return { tableName, schema: schemaResponse.data, rows: rowsResponse.data.rows }
    }),
  )

  payloads.forEach(({ tableName, schema, rows }) => {
    tableSchemas[tableName] = schema
    tableRows[tableName] = rows
  })

  recentEvents.value = (await fetchRecentRecordEvents()).data.events

  if (!selectedProductCode.value && productRows.value[0]) {
    selectedProductCode.value = String(productRows.value[0].product_code ?? '')
  }
  if (!selectedOrderNo.value && orderRows.value[0]) {
    selectedOrderNo.value = String(orderRows.value[0].order_no ?? '')
  }
  if (selectedProductCode.value && !selectedProduct.value && productRows.value[0]) {
    selectedProductCode.value = String(productRows.value[0].product_code ?? '')
  }
  if (selectedOrderNo.value && !selectedOrder.value && orderRows.value[0]) {
    selectedOrderNo.value = String(orderRows.value[0].order_no ?? '')
  }
}

const refreshAll = async () => {
  loading.value = true
  try {
    await loadAllTablesData()
  } finally {
    loading.value = false
  }
}

const selectTable = (tableName: string) => {
  currentTable.value = tableName
}

const handleProductRowClick = (row: Record<string, unknown>) => {
  selectedProductCode.value = String(row.product_code ?? '')
}

const handleOrderRowClick = (row: Record<string, unknown>) => {
  selectedOrderNo.value = String(row.order_no ?? '')
}

const openCreateDialog = (tableName: string) => {
  editorTableName.value = tableName
  editingMode.value = 'create'
  editingRecordId.value = ''

  editableFieldsForTable(tableName).forEach((field) => {
    if (tableName === 'product_bom' && field.name === 'product_code' && selectedProductCode.value) {
      draftValues[field.name] = selectedProductCode.value
      return
    }
    if (tableName === 'customer_order') {
      if (field.name === 'product_code' && selectedProduct.value) {
        draftValues[field.name] = String(selectedProduct.value.product_code ?? '')
        return
      }
      if (field.name === 'product_name' && selectedProduct.value) {
        draftValues[field.name] = String(selectedProduct.value.product_name ?? '')
        return
      }
      if (field.name === 'unit_price' && selectedProduct.value) {
        draftValues[field.name] = Number(selectedProduct.value.unit_price ?? 0)
        return
      }
      if (field.name === 'ordered_qty') {
        draftValues[field.name] = 1
        return
      }
      if (field.name === 'order_status') {
        draftValues[field.name] = 'draft'
        return
      }
    }
    if (tableName === 'product_bom') {
      if (field.name === 'source_type') {
        draftValues[field.name] = 'purchase'
        return
      }
      if (field.name === 'source_ref') {
        draftValues[field.name] = BOM_SOURCE_REF_OPTIONS.purchase[0]?.value ?? ''
        return
      }
    }
    draftValues[field.name] = field.field_type === 'number' ? 0 : ''
  })

  ensureBomDraftSourceFields()

  editorVisible.value = true
}

const openEditDialog = (tableName: string, row: Record<string, unknown>) => {
  editorTableName.value = tableName
  editingMode.value = 'edit'
  editingRecordId.value = String(row.id ?? '')

  editableFieldsForTable(tableName).forEach((field) => {
    draftValues[field.name] = normalizeValueForField(field, row[field.name])
  })

  ensureBomDraftSourceFields()

  editorVisible.value = true
}

const submitEditor = async () => {
  if (!editorTableName.value) return
  saving.value = true
  try {
    ensureBomDraftSourceFields()
    const payload = editorFields.value.reduce<Record<string, unknown>>((accumulator, field) => {
      if (editorTableName.value === 'product_bom' && field.name === 'source_type') {
        accumulator[field.name] = normalizeBomSourceType(draftValues[field.name])
        return accumulator
      }
      accumulator[field.name] = normalizeValueForField(field, draftValues[field.name])
      return accumulator
    }, {})

    const response = editingMode.value === 'create'
      ? await createRecordRow(editorTableName.value, payload)
      : await updateRecordRow(editorTableName.value, editingRecordId.value, payload)

    lastMutationSummary.value = `事件 ${response.data.change_event_id} 已触发，execution ${response.data.triggered_execution_ids.join(', ') || '无'}`
    editorVisible.value = false
    ElMessage.success('记录已保存并刷新闭环数据')
    await refreshAll()
  } finally {
    saving.value = false
  }
}

const removeRow = async (tableName: string, row: Record<string, unknown>) => {
  try {
    await ElMessageBox.confirm('删除后会同步刷新这条业务链路的派生表，确认继续？', '删除记录', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  const response = await deleteRecordRow(tableName, String(row.id ?? ''))
  lastMutationSummary.value = `事件 ${response.data.change_event_id} 已触发，execution ${response.data.triggered_execution_ids.join(', ') || '无'}`
  ElMessage.success('记录已删除并刷新闭环数据')
  await refreshAll()
}

onMounted(async () => {
  await refreshAll()
})
</script>
