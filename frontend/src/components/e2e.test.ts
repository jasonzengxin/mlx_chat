import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ExportModal from './ExportModal.vue'
import TemplateEditor from './TemplateEditor.vue'

// Mock global fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock the export API module
vi.mock('@/api/export', () => ({
  getExportTemplates: vi.fn().mockResolvedValue([
    { id: 'tpl-1', name: '学习笔记', description: 'For study', language: 'zh', is_builtin: true, template_content: '# Test', system_prompt: 'Test', created_at: '', updated_at: '' },
    { id: 'tpl-2', name: 'My Template', description: 'Custom', language: 'en', is_builtin: false, template_content: '# Custom', system_prompt: 'Summarize', created_at: '', updated_at: '' },
  ]),
  estimateExport: vi.fn().mockResolvedValue({ estimated_tokens: 150, message_count: 10, is_remote: false, warning: null }),
  streamingExport: vi.fn().mockResolvedValue({ total_chars: 100, duration_ms: 500, ttft_ms: 50, content: '# Summary\n\nContent' }),
}))

import { getExportTemplates, estimateExport } from '@/api/export'

// ── ExportModal Tests ────────────────────────────────────

describe('ExportModal Component', () => {
  const defaultProps = {
    show: false,
    sessionId: 'test-session-id',
    sessionName: 'Test Session',
  }

  function createWrapper(props = {}) {
    return mount(ExportModal, {
      props: { ...defaultProps, ...props },
      global: {
        stubs: {
          Modal: { template: '<div class="modal-stub"><slot /><slot name="footer" /></div>' }
        }
      }
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial state', () => {
    it('should start at select step when opened', async () => {
      const wrapper = createWrapper()
      await wrapper.setProps({ show: true })
      await wrapper.vm.$nextTick()
      const vm = wrapper.vm as any
      expect(vm.step).toBe('select')
    })

    it('should reset state when opened', async () => {
      const wrapper = createWrapper()
      // Open modal
      await wrapper.setProps({ show: true })
      await wrapper.vm.$nextTick()

      const vm = wrapper.vm as any
      expect(vm.selectedTemplateId).toBeNull()
      expect(vm.language).toBe('zh')
      expect(vm.estimate).toBeNull()
      expect(vm.previewContent).toBe('')
    })
  })

  describe('Template loading', () => {
    it('should load templates when opened', async () => {
      const wrapper = createWrapper()
      await wrapper.setProps({ show: true })
      await vi.waitFor(() => {
        expect(getExportTemplates).toHaveBeenCalled()
      })
    })

    it('should display loaded templates', async () => {
      const wrapper = createWrapper()
      await wrapper.setProps({ show: true })
      await vi.waitFor(() => {
        expect((wrapper.vm as any).templates.length).toBe(2)
      })
      const cards = wrapper.findAll('.template-card')
      expect(cards.length).toBe(2)
    })
  })

  describe('Template selection', () => {
    it('should select template on card click', async () => {
      const wrapper = createWrapper()
      await wrapper.setProps({ show: true })
      await vi.waitFor(() => {
        expect((wrapper.vm as any).templates.length).toBe(2)
      })

      const firstCard = wrapper.findAll('.template-card').at(0)
      await firstCard!.trigger('click')

      const vm = wrapper.vm as any
      expect(vm.selectedTemplateId).toBe('tpl-1')
    })

    it('should show Next button disabled when no template selected', async () => {
      const wrapper = createWrapper({ show: false })
      await wrapper.setProps({ show: true })
      await vi.waitFor(() => {})

      // Next button should be disabled when no template selected
      const nextBtn = wrapper.findAll('.primary-btn').at(0)
      expect(nextBtn!.attributes('disabled')).toBeDefined()
    })
  })

  describe('Estimate flow', () => {
    it('should transition to confirm step after estimate', async () => {
      const wrapper = createWrapper()
      await wrapper.setProps({ show: true })
      await vi.waitFor(() => {
        expect((wrapper.vm as any).templates.length).toBe(2)
      })

      const vm = wrapper.vm as any
      vm.selectedTemplateId = 'tpl-1'
      vm.language = 'zh'
      await vm.handleEstimate()

      expect(vm.step).toBe('confirm')
    })

    it('should call estimateExport API', async () => {
      const wrapper = createWrapper()
      await wrapper.setProps({ show: true })
      await vi.waitFor(() => {
        expect((wrapper.vm as any).templates.length).toBe(2)
      })

      const vm = wrapper.vm as any
      vm.selectedTemplateId = 'tpl-1'
      vm.language = 'en'
      await vm.handleEstimate()

      expect(estimateExport).toHaveBeenCalledWith('test-session-id', 'tpl-1', 'en')
    })

    it('should populate estimate data after API returns', async () => {
      const wrapper = createWrapper()
      await wrapper.setProps({ show: true })
      await vi.waitFor(() => {
        expect((wrapper.vm as any).templates.length).toBe(2)
      })

      const vm = wrapper.vm as any
      vm.selectedTemplateId = 'tpl-1'
      vm.language = 'zh'
      await vm.handleEstimate()

      await vi.waitFor(() => {
        expect((wrapper.vm as any).estimate).not.toBeNull()
      })
      expect((wrapper.vm as any).estimate!.estimated_tokens).toBe(150)
    })
  })

  describe('Cancel generation', () => {
    it('should go back to select step on cancel', async () => {
      const wrapper = createWrapper()
      const vm = wrapper.vm as any
      vm.step = 'generating'
      vm.previewContent = 'partial'
      await vm.cancelGeneration()
      expect(vm.step).toBe('select')
      expect(vm.previewContent).toBe('')
    })

    it('should abort the request when cancelled', async () => {
      const wrapper = createWrapper()
      const vm = wrapper.vm as any
      vm.abortController = { abort: vi.fn() }
      await vm.cancelGeneration()
      expect((vm.abortController as any)?.abort).toHaveBeenCalled()
    })
  })

  describe('formatLanguage helper', () => {
    it('when output language is zh, uses Chinese labels for template language badges', () => {
      const wrapper = createWrapper()
      const vm = wrapper.vm as any
      vm.language = 'zh'
      expect(vm.formatLanguage('both')).toBe('中英')
      expect(vm.formatLanguage('zh')).toBe('中文')
      expect(vm.formatLanguage('en')).toBe('英文')
    })

    it('when output language is en, uses English labels for template language badges', () => {
      const wrapper = createWrapper()
      const vm = wrapper.vm as any
      vm.language = 'en'
      expect(vm.formatLanguage('both')).toBe('CN / EN')
      expect(vm.formatLanguage('zh')).toBe('Chinese')
      expect(vm.formatLanguage('en')).toBe('English')
    })
  })

  describe('Close handling', () => {
    it('should emit close event', async () => {
      const wrapper = createWrapper()
      await wrapper.vm.handleClose()
      expect(wrapper.emitted('close')).toBeTruthy()
    })

    it('should not emit close while generating', async () => {
      const wrapper = createWrapper()
      const vm = wrapper.vm as any
      vm.step = 'generating'
      await vm.handleClose()
      // handleClose returns early when generating, no close emitted
      expect(wrapper.emitted('close')).toBeFalsy()
    })
  })
})

// ── TemplateEditor Tests ─────────────────────────────────

describe('TemplateEditor Component', () => {
  const defaultModelValue = {
    name: 'Test Template',
    description: 'Test description',
    language: 'both',
    system_prompt: 'Summarize the conversation.',
    template_content: '# Test',
  }

  function createWrapper(modelValue = {}) {
    return mount(TemplateEditor, {
      props: {
        modelValue: { ...defaultModelValue, ...modelValue }
      }
    })
  }

  describe('Field rendering', () => {
    it('should display name in first input', () => {
      const wrapper = createWrapper()
      const nameInput = wrapper.find('input[type="text"]')
      expect(nameInput.element.value).toBe('Test Template')
    })

    it('should display description in second input', () => {
      const wrapper = createWrapper()
      const inputs = wrapper.findAll('input[type="text"]')
      expect(inputs.at(1).element.value).toBe('Test description')
    })
  })

  describe('v-model updates', () => {
    it('should emit update when name changes', async () => {
      const wrapper = createWrapper()
      const nameInput = wrapper.find('input[type="text"]')
      await nameInput.setValue('New Name')
      const emitted = wrapper.emitted('update:modelValue')![0][0] as any
      expect(emitted.name).toBe('New Name')
    })

    it('should emit update when description changes', async () => {
      const wrapper = createWrapper()
      const inputs = wrapper.findAll('input[type="text"]')
      await inputs.at(1).setValue('New desc')
      const emitted = wrapper.emitted('update:modelValue')![0][0] as any
      expect(emitted.description).toBe('New desc')
    })

    it('should emit update when system prompt changes', async () => {
      const wrapper = createWrapper()
      const textarea = wrapper.find('textarea')
      await textarea.setValue('New prompt')
      const emitted = wrapper.emitted('update:modelValue')![0][0] as any
      expect(emitted.system_prompt).toBe('New prompt')
    })
  })

  describe('Language selector', () => {
    it('should have three options', () => {
      const wrapper = createWrapper()
      const options = wrapper.findAll('select option')
      expect(options.length).toBe(3)
    })

    it('should emit update when language changes', async () => {
      const wrapper = createWrapper()
      const select = wrapper.find('select')
      await select.setValue('en')
      const emitted = wrapper.emitted('update:modelValue')![0][0] as any
      expect(emitted.language).toBe('en')
    })
  })

  describe('Placeholder reference', () => {
    it('should toggle visibility on click', async () => {
      const wrapper = createWrapper()
      expect((wrapper.vm as any).showRef).toBe(false)
      await wrapper.find('.ref-header').trigger('click')
      expect((wrapper.vm as any).showRef).toBe(true)
    })

    it('should show placeholder items when open', async () => {
      const wrapper = createWrapper()
      await wrapper.find('.ref-header').trigger('click')
      const items = wrapper.findAll('.ref-item')
      expect(items.length).toBeGreaterThan(0)
    })

    it('should insert placeholder into template content', async () => {
      const wrapper = createWrapper()
      await wrapper.find('.ref-header').trigger('click')
      const items = wrapper.findAll('.ref-item')
      await items.at(0).trigger('click')
      const vm = wrapper.vm as any
      expect(vm.templateContent).toContain('{{session_name}}')
    })
  })
})
