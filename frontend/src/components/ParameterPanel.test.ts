import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ParameterPanel from './ParameterPanel.vue'

describe('ParameterPanel Component', () => {
  const defaultProps = {
    show: true,
    temperature: 0.7,
    maxTokens: 4096,
    systemPrompt: ''
  }

  function createWrapper(props = {}) {
    return mount(ParameterPanel, {
      props: { ...defaultProps, ...props }
    })
  }

  describe('Visibility', () => {
    it('should render when show is true', () => {
      const wrapper = createWrapper({ show: true })
      expect(wrapper.find('.parameter-panel').exists()).toBe(true)
    })

    it('should not render when show is false', () => {
      const wrapper = createWrapper({ show: false })
      expect(wrapper.find('.parameter-panel').exists()).toBe(false)
    })

    it('should emit close when close button is clicked', async () => {
      const wrapper = createWrapper()
      await wrapper.find('.close-btn').trigger('click')
      expect(wrapper.emitted('close')).toBeTruthy()
    })
  })

  describe('Temperature slider', () => {
    it('should display current temperature value', () => {
      const wrapper = createWrapper({ temperature: 1.5 })
      expect(wrapper.find('.param-value').text()).toBe('1.5')
    })

    it('should emit update:temperature when slider changes', async () => {
      const wrapper = createWrapper({ temperature: 0.7 })
      const slider = wrapper.find('.slider')

      await slider.setValue(1.2)
      expect(wrapper.emitted('update:temperature')).toBeTruthy()
      expect(wrapper.emitted('update:temperature')![0]).toEqual([1.2])
    })
  })

  describe('Max Tokens input', () => {
    it('should display current max tokens value', () => {
      const wrapper = createWrapper({ maxTokens: 2048 })
      const input = wrapper.find('.input-field')
      expect(input.element.value).toBe('2048')
    })

    it('should emit update:maxTokens when input changes', async () => {
      const wrapper = createWrapper({ maxTokens: 4096 })
      const input = wrapper.find('.input-field')

      await input.setValue('2048')
      expect(wrapper.emitted('update:maxTokens')).toBeTruthy()
      expect(wrapper.emitted('update:maxTokens')![0]).toEqual([2048])
    })
  })

  describe('System Prompt textarea', () => {
    it('should display current system prompt', () => {
      const wrapper = createWrapper({ systemPrompt: 'Test prompt' })
      const textarea = wrapper.find('.textarea-field')
      expect(textarea.element.value).toBe('Test prompt')
    })

    it('should emit update:systemPrompt when changed', async () => {
      const wrapper = createWrapper({ systemPrompt: '' })
      const textarea = wrapper.find('.textarea-field')

      await textarea.setValue('New prompt')
      expect(wrapper.emitted('update:systemPrompt')).toBeTruthy()
      expect(wrapper.emitted('update:systemPrompt')![0]).toEqual(['New prompt'])
    })

    it('should show clear button when system prompt is not empty', () => {
      const wrapper = createWrapper({ systemPrompt: 'Some text' })
      expect(wrapper.find('.clear-btn').exists()).toBe(true)
    })

    it('should not show clear button when system prompt is empty', () => {
      const wrapper = createWrapper({ systemPrompt: '' })
      expect(wrapper.find('.clear-btn').exists()).toBe(false)
    })

    it('should emit empty string when clear button is clicked', async () => {
      const wrapper = createWrapper({ systemPrompt: 'Some text' })
      await wrapper.find('.clear-btn').trigger('click')
      expect(wrapper.emitted('update:systemPrompt')).toBeTruthy()
      expect(wrapper.emitted('update:systemPrompt')![0]).toEqual([''])
    })
  })

  describe('Reset button', () => {
    it('should emit default values when reset is clicked', async () => {
      const wrapper = createWrapper({
        temperature: 1.5,
        maxTokens: 2048,
        systemPrompt: 'Custom prompt'
      })

      await wrapper.find('.reset-btn').trigger('click')

      // Check all three parameters are reset
      expect(wrapper.emitted('update:temperature')).toBeTruthy()
      expect(wrapper.emitted('update:temperature')![0]).toEqual([0.7])

      expect(wrapper.emitted('update:maxTokens')).toBeTruthy()
      expect(wrapper.emitted('update:maxTokens')![0]).toEqual([4096])

      expect(wrapper.emitted('update:systemPrompt')).toBeTruthy()
      expect(wrapper.emitted('update:systemPrompt')![0]).toEqual([''])
    })
  })

  describe('Max tokens validation', () => {
    it('should clamp max tokens to 1-8192 range', async () => {
      const wrapper = createWrapper({ maxTokens: 4096 })
      const input = wrapper.find('.input-field')

      // Test boundary: value > 8192 should be clamped
      await input.setValue('10000')
      const emitted = wrapper.emitted('update:maxTokens')?.[0]
      expect(emitted?.[0]).toBe(8192)
    })
  })

  describe('Panel header', () => {
    it('should display "Parameters" title', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('.panel-header h3').text()).toBe('Parameters')
    })
  })
})
