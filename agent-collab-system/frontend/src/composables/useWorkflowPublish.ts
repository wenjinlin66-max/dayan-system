import { ElMessage } from 'element-plus'
import { computed } from 'vue'

import {
  compileWorkflow,
  createWorkflow,
  deleteWorkflow,
  fetchWorkflows,
  fetchWorkflowVersions,
  publishWorkflow,
  saveWorkflowDraft,
} from '@/api/workflows'
import { useWorkflowStore } from '@/store/workflow'
import { mapCanvasToDsl } from '@/utils/canvasMapper'
import type { DialogNodeConfig, WorkflowDialogTriggerConfig, WorkflowNode } from '@/types/workflow'

const extractErrorMessage = (error: unknown) => {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (detail === 'WORKFLOW_CODE_ALREADY_EXISTS') {
    return '工作流编码已存在，请更换一个新的编码后再保存。'
  }
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  return String(error)
}

export const useWorkflowPublish = () => {
  const workflowStore = useWorkflowStore()
  const canPublish = computed(() => workflowStore.compileResult?.compile_status === 'success' && !workflowStore.compileStale)

  const buildUiSchema = () => mapCanvasToDsl(workflowStore.nodes, workflowStore.edges)

  const findDialogNode = (): WorkflowNode | undefined => workflowStore.nodes.find((node) => node.type === 'dialog_agent')

  const buildDialogTriggerConfig = (): WorkflowDialogTriggerConfig | undefined => {
    if (workflowStore.workflowCategory !== 'dialog_trigger') {
      return undefined
    }
    const dialogNode = findDialogNode()
    if (!dialogNode) {
      return undefined
    }
    const config = dialogNode.config as DialogNodeConfig
    return {
      summary: typeof config.triggerSummary === 'string' ? config.triggerSummary : '',
      synonyms: Array.isArray(config.triggerSynonyms) ? config.triggerSynonyms.filter((item): item is string => typeof item === 'string' && item.trim().length > 0) : [],
      example_utterances: Array.isArray(config.triggerExampleUtterances) ? config.triggerExampleUtterances.filter((item): item is string => typeof item === 'string' && item.trim().length > 0) : [],
      allowed_roles: Array.isArray(config.triggerAllowedRoles) ? config.triggerAllowedRoles.filter((item): item is string => typeof item === 'string' && item.trim().length > 0) : [],
      required_inputs: Array.isArray(config.triggerRequiredInputs) ? config.triggerRequiredInputs.filter((item): item is string => typeof item === 'string' && item.trim().length > 0) : [],
      input_schema: config.triggerInputSchema && typeof config.triggerInputSchema === 'object' ? config.triggerInputSchema : null,
    }
  }

  const withActionLock = async <T>(action: 'save' | 'compile' | 'publish' | 'load', runner: () => Promise<T>) => {
    if (workflowStore.isBusy) {
      ElMessage.warning('当前有操作正在执行，请稍候。')
      return null
    }

    workflowStore.setActiveAction(action)
    try {
      return await runner()
    } finally {
      workflowStore.setActiveAction('')
    }
  }

  const ensureWorkflow = async () => {
    if (workflowStore.currentWorkflowId) {
      return workflowStore.currentWorkflowId
    }

    const response = await createWorkflow({
      name: workflowStore.workflowName,
      code: workflowStore.workflowCode,
      visibility: 'private',
      owner_dept_id: workflowStore.ownerDeptId,
      ui_schema: workflowStore.uiSchema,
    })
    workflowStore.setWorkflowMeta({ workflowId: response.data.workflow_id })
    return response.data.workflow_id as string
  }

  const refreshVersions = async () => {
    if (!workflowStore.currentWorkflowId) {
      return
    }
    const versionsRes = await fetchWorkflowVersions(workflowStore.currentWorkflowId, { dept_id: workflowStore.ownerDeptId })
    const versions = versionsRes.data.versions
    const releaseFromVersions = versions.find((item: { is_current_release: boolean }) => item.is_current_release) ?? null

    workflowStore.setVersions(versions)
    workflowStore.setCurrentRelease(releaseFromVersions)
  }

  const refreshWorkflowList = async () => {
    const res = await fetchWorkflows({ include_all: true })
    workflowStore.setAvailableWorkflows(res.data)
  }

  const loadWorkflow = async (workflowId: string) => {
    await withActionLock('load', async () => {
      const requestedWorkflowId = workflowId
      const list = workflowStore.availableWorkflows.length > 0 ? workflowStore.availableWorkflows : (await fetchWorkflows({ include_all: true })).data
      const summary = list.find((item: { workflow_id: string }) => item.workflow_id === requestedWorkflowId)
      if (!summary) {
        ElMessage.error('未找到对应 workflow')
        return
      }

      const deptId = summary.owner_dept_id
      workflowStore.setWorkflowMeta({ ownerDeptId: summary.owner_dept_id as typeof workflowStore.ownerDeptId })
      const versions = (await fetchWorkflowVersions(requestedWorkflowId, { dept_id: deptId })).data.versions

      if (!versions.length) {
        ElMessage.error('加载 workflow 失败')
        return
      }

      const release = versions.find((item: { is_current_release: boolean }) => item.is_current_release) ?? null
      const draftFromVersions = versions
        .filter((item: { mode: string }) => item.mode === 'draft')
        .sort((left: { version: number }, right: { version: number }) => right.version - left.version)[0] ?? null
      const hydratedDraft = draftFromVersions ?? release

      if (!hydratedDraft) {
        ElMessage.error('未找到可恢复的 workflow 草稿或发布版本')
        return
      }

      workflowStore.loadWorkflow({
        summary,
        draft: hydratedDraft,
        release,
        versions,
      })
    })
  }

  const saveDraft = async () => {
    await withActionLock('save', async () => {
      try {
        const workflowId = await ensureWorkflow()
        const response = await saveWorkflowDraft(workflowId, {
          name: workflowStore.workflowName,
          ui_schema: buildUiSchema(),
        }, { dept_id: workflowStore.ownerDeptId })
        workflowStore.setDraftSnapshot(response.data)
        await refreshVersions()
        ElMessage.success('草稿已保存')
      } catch (error) {
        ElMessage.error(`保存草稿失败：${extractErrorMessage(error)}`)
      }
    })
  }

  const compile = async () => {
    await withActionLock('compile', async () => {
      try {
        const workflowId = await ensureWorkflow()
        await saveWorkflowDraft(workflowId, {
          name: workflowStore.workflowName,
          ui_schema: buildUiSchema(),
        }, { dept_id: workflowStore.ownerDeptId })
        const response = await compileWorkflow(workflowId, { dept_id: workflowStore.ownerDeptId })
        workflowStore.setCompileResult(response.data)
        await refreshVersions()
        if (response.data.compile_status === 'success') {
          ElMessage.success('编译成功')
        } else {
          ElMessage.warning('编译完成，但存在错误')
        }
      } catch (error) {
        ElMessage.error(`编译失败：${extractErrorMessage(error)}`)
      }
    })
  }

  const publish = async () => {
    await withActionLock('publish', async () => {
      try {
        if (!canPublish.value) {
          ElMessage.warning('请先编译成功，再执行发布')
          return
        }
        const workflowId = await ensureWorkflow()
        const response = await publishWorkflow(workflowId, {
          category: workflowStore.workflowCategory,
          summary: buildDialogTriggerConfig()?.summary || `${workflowStore.workflowName} 最小闭环流程`,
          dialog_trigger_config: buildDialogTriggerConfig(),
          dept_id: workflowStore.ownerDeptId,
        })
        workflowStore.setCurrentRelease(response.data)
        await refreshVersions()
        ElMessage.success('发布成功')
      } catch (error) {
        ElMessage.error(`发布失败：${extractErrorMessage(error)}`)
      }
    })
  }

  const removeWorkflow = async (workflowId: string) => {
    if (!workflowId) {
      return
    }
    await withActionLock('load', async () => {
      const matched = workflowStore.availableWorkflows.find((item) => item.workflow_id === workflowId)
      await deleteWorkflow(workflowId, { dept_id: matched?.owner_dept_id ?? workflowStore.ownerDeptId })
      if (workflowStore.currentWorkflowId === workflowId) {
        workflowStore.resetWorkflowEditor()
        workflowStore.ensureDraftMeta()
      }
      await refreshWorkflowList()
      ElMessage.success('工作流已删除')
    })
  }

  return {
    canPublish,
    saveDraft,
    compile,
    publish,
    removeWorkflow,
    refreshVersions,
    refreshWorkflowList,
    loadWorkflow,
  }
}
