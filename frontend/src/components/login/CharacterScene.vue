<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps<{
  isTyping: boolean
  passwordVisible: boolean
  hasPassword: boolean
}>()

// 鼠标位置
const mouseX = ref(0)
const mouseY = ref(0)

// 眨眼状态
const isPurpleBlinking = ref(false)
const isBlackBlinking = ref(false)

// 角色互动状态
const isLookingAtEachOther = ref(false)
const isPurplePeeking = ref(false)

// 角色身体元素引用
const purpleRef = ref<HTMLElement | null>(null)
const blackRef = ref<HTMLElement | null>(null)
const orangeRef = ref<HTMLElement | null>(null)
const yellowRef = ref<HTMLElement | null>(null)

// 每只眼球的独立 ref（用于瞳孔追踪）
const purpleEyeL = ref<HTMLElement | null>(null)
const purpleEyeR = ref<HTMLElement | null>(null)
const blackEyeL = ref<HTMLElement | null>(null)
const blackEyeR = ref<HTMLElement | null>(null)
const orangeEyeL = ref<HTMLElement | null>(null)
const orangeEyeR = ref<HTMLElement | null>(null)
const yellowEyeL = ref<HTMLElement | null>(null)
const yellowEyeR = ref<HTMLElement | null>(null)

// 定时器引用
let purpleBlinkTimeout: ReturnType<typeof setTimeout> | null = null
let blackBlinkTimeout: ReturnType<typeof setTimeout> | null = null
let lookTimeout: ReturnType<typeof setTimeout> | null = null
let peekTimeout: ReturnType<typeof setTimeout> | null = null
let rafId: number | null = null

// 鼠标移动处理（RAF 节流）
let pendingMouseX = 0
let pendingMouseY = 0

function onMouseMove(e: MouseEvent) {
  pendingMouseX = e.clientX
  pendingMouseY = e.clientY
  if (!rafId) {
    rafId = requestAnimationFrame(() => {
      mouseX.value = pendingMouseX
      mouseY.value = pendingMouseY
      rafId = null
    })
  }
}

// 计算角色身体位置偏移（脸部整体移动 + 身体倾斜）
function calcBody(el: HTMLElement | null) {
  if (!el) return { faceX: 0, faceY: 0, bodySkew: 0 }
  const rect = el.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 3
  const dx = mouseX.value - cx
  const dy = mouseY.value - cy
  return {
    faceX: Math.max(-15, Math.min(15, dx / 20)),
    faceY: Math.max(-10, Math.min(10, dy / 30)),
    bodySkew: Math.max(-6, Math.min(6, -dx / 120)),
  }
}

// 计算单个眼球的瞳孔偏移（基于眼球元素位置跟踪鼠标）
function calcPupil(eyeEl: HTMLElement | null, maxDist: number = 5) {
  if (!eyeEl) return { x: 0, y: 0 }
  const rect = eyeEl.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  const dx = mouseX.value - cx
  const dy = mouseY.value - cy
  const dist = Math.min(Math.sqrt(dx * dx + dy * dy), maxDist)
  const angle = Math.atan2(dy, dx)
  return {
    x: Math.cos(angle) * dist,
    y: Math.sin(angle) * dist,
  }
}

// 获取紫色角色瞳孔偏移
function purplePupil(eyeEl: HTMLElement | null) {
  if (props.hasPassword && props.passwordVisible) {
    return { x: isPurplePeeking.value ? 4 : -4, y: isPurplePeeking.value ? 5 : -4 }
  }
  if (isLookingAtEachOther.value) {
    return { x: 3, y: 4 }
  }
  return calcPupil(eyeEl, 5)
}

// 获取黑色角色瞳孔偏移
function blackPupil(eyeEl: HTMLElement | null) {
  if (props.hasPassword && props.passwordVisible) {
    return { x: -4, y: -4 }
  }
  if (isLookingAtEachOther.value) {
    return { x: 0, y: -4 }
  }
  return calcPupil(eyeEl, 4)
}

// 获取橙色角色瞳孔偏移
function orangePupil(eyeEl: HTMLElement | null) {
  if (props.hasPassword && props.passwordVisible) {
    return { x: -5, y: -4 }
  }
  return calcPupil(eyeEl, 5)
}

// 获取黄色角色瞳孔偏移
function yellowPupil(eyeEl: HTMLElement | null) {
  if (props.hasPassword && props.passwordVisible) {
    return { x: -5, y: -4 }
  }
  return calcPupil(eyeEl, 5)
}

// 眨眼调度
function schedulePurpleBlink() {
  const interval = Math.random() * 4000 + 3000
  purpleBlinkTimeout = setTimeout(() => {
    isPurpleBlinking.value = true
    setTimeout(() => {
      isPurpleBlinking.value = false
      schedulePurpleBlink()
    }, 150)
  }, interval)
}

function scheduleBlackBlink() {
  const interval = Math.random() * 4000 + 3000
  blackBlinkTimeout = setTimeout(() => {
    isBlackBlinking.value = true
    setTimeout(() => {
      isBlackBlinking.value = false
      scheduleBlackBlink()
    }, 150)
  }, interval)
}

// 打字时角色互相看
watch(() => props.isTyping, (typing) => {
  if (typing) {
    isLookingAtEachOther.value = true
    if (lookTimeout) clearTimeout(lookTimeout)
    lookTimeout = setTimeout(() => {
      isLookingAtEachOther.value = false
    }, 800)
  } else {
    isLookingAtEachOther.value = false
  }
})

// 紫色角色偷看密码
watch([() => props.hasPassword, () => props.passwordVisible], ([hasPass, visible]) => {
  if (peekTimeout) clearTimeout(peekTimeout)
  if (hasPass && visible) {
    schedulePeek()
  } else {
    isPurplePeeking.value = false
  }
})

function schedulePeek() {
  const interval = Math.random() * 3000 + 2000
  peekTimeout = setTimeout(() => {
    isPurplePeeking.value = true
    setTimeout(() => {
      isPurplePeeking.value = false
      if (props.hasPassword && props.passwordVisible) {
        schedulePeek()
      }
    }, 800)
  }, interval)
}

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  schedulePurpleBlink()
  scheduleBlackBlink()
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  if (purpleBlinkTimeout) clearTimeout(purpleBlinkTimeout)
  if (blackBlinkTimeout) clearTimeout(blackBlinkTimeout)
  if (lookTimeout) clearTimeout(lookTimeout)
  if (peekTimeout) clearTimeout(peekTimeout)
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<template>
  <div class="relative w-full h-full bg-gradient-to-br from-[#1a0a3e]/90 via-[#6C3FF5]/30 to-[#1a0a3e]/80 rounded-l-2xl overflow-hidden">
    <!-- 网格装饰 -->
    <div class="absolute inset-0 bg-[size:20px_20px]" style="background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);" />
    <!-- 光晕 -->
    <div class="absolute top-1/4 right-1/4 w-64 h-64 bg-[#6C3FF5]/20 rounded-full blur-3xl" />
    <div class="absolute bottom-1/4 left-1/4 w-96 h-96 bg-[#E8D754]/10 rounded-full blur-3xl" />

    <!-- 角色舞台 -->
    <div class="absolute inset-0 flex items-end justify-center pb-8">
      <div class="relative" style="width: 550px; height: 400px;">

        <!-- 紫色高个角色 -->
        <div
          ref="purpleRef"
          class="absolute bottom-0 transition-all duration-700 ease-in-out"
          :style="{
            left: '70px',
            width: '180px',
            height: (props.isTyping || (props.hasPassword && !props.passwordVisible)) ? '440px' : '400px',
            backgroundColor: '#6C3FF5',
            borderRadius: '10px 10px 0 0',
            zIndex: 1,
            transform: (props.hasPassword && props.passwordVisible)
              ? 'skewX(0deg)'
              : (props.isTyping || (props.hasPassword && !props.passwordVisible))
                ? `skewX(${(calcBody(purpleRef).bodySkew || 0) - 12}deg) translateX(40px)`
                : `skewX(${calcBody(purpleRef).bodySkew || 0}deg)`,
            transformOrigin: 'bottom center',
          }"
        >
          <!-- 眼睛容器 -->
          <div
            class="absolute flex gap-8 transition-all duration-700 ease-in-out"
            :style="{
              left: (props.hasPassword && props.passwordVisible) ? '20px' : isLookingAtEachOther ? '55px' : `${45 + calcBody(purpleRef).faceX}px`,
              top: (props.hasPassword && props.passwordVisible) ? '35px' : isLookingAtEachOther ? '65px' : `${40 + calcBody(purpleRef).faceY}px`,
            }"
          >
            <!-- 左眼白 -->
            <div
              ref="purpleEyeL"
              class="rounded-full flex items-center justify-center transition-all duration-150"
              :style="{
                width: '18px',
                height: isPurpleBlinking ? '2px' : '18px',
                backgroundColor: 'white',
                overflow: 'hidden',
              }"
            >
              <!-- 左瞳孔 -->
              <div
                v-if="!isPurpleBlinking"
                class="rounded-full"
                :style="{
                  width: '7px',
                  height: '7px',
                  backgroundColor: '#2D2D2D',
                  transform: `translate(${purplePupil(purpleEyeL).x}px, ${purplePupil(purpleEyeL).y}px)`,
                  transition: 'transform 0.1s ease-out',
                }"
              />
            </div>
            <!-- 右眼白 -->
            <div
              ref="purpleEyeR"
              class="rounded-full flex items-center justify-center transition-all duration-150"
              :style="{
                width: '18px',
                height: isPurpleBlinking ? '2px' : '18px',
                backgroundColor: 'white',
                overflow: 'hidden',
              }"
            >
              <div
                v-if="!isPurpleBlinking"
                class="rounded-full"
                :style="{
                  width: '7px',
                  height: '7px',
                  backgroundColor: '#2D2D2D',
                  transform: `translate(${purplePupil(purpleEyeR).x}px, ${purplePupil(purpleEyeR).y}px)`,
                  transition: 'transform 0.1s ease-out',
                }"
              />
            </div>
          </div>
        </div>

        <!-- 黑色高个角色 -->
        <div
          ref="blackRef"
          class="absolute bottom-0 transition-all duration-700 ease-in-out"
          :style="{
            left: '240px',
            width: '120px',
            height: '310px',
            backgroundColor: '#111827',
            borderRadius: '8px 8px 0 0',
            zIndex: 2,
            transform: (props.hasPassword && props.passwordVisible)
              ? 'skewX(0deg)'
              : isLookingAtEachOther
                ? `skewX(${(calcBody(blackRef).bodySkew || 0) * 1.5 + 10}deg) translateX(20px)`
                : (props.isTyping || (props.hasPassword && !props.passwordVisible))
                  ? `skewX(${(calcBody(blackRef).bodySkew || 0) * 1.5}deg)`
                  : `skewX(${calcBody(blackRef).bodySkew || 0}deg)`,
            transformOrigin: 'bottom center',
          }"
        >
          <div
            class="absolute flex gap-6 transition-all duration-700 ease-in-out"
            :style="{
              left: (props.hasPassword && props.passwordVisible) ? '10px' : isLookingAtEachOther ? '32px' : `${26 + calcBody(blackRef).faceX}px`,
              top: (props.hasPassword && props.passwordVisible) ? '28px' : isLookingAtEachOther ? '12px' : `${32 + calcBody(blackRef).faceY}px`,
            }"
          >
            <div
              ref="blackEyeL"
              class="rounded-full flex items-center justify-center transition-all duration-150"
              :style="{
                width: '16px',
                height: isBlackBlinking ? '2px' : '16px',
                backgroundColor: 'white',
                overflow: 'hidden',
              }"
            >
              <div
                v-if="!isBlackBlinking"
                class="rounded-full"
                :style="{
                  width: '6px',
                  height: '6px',
                  backgroundColor: '#2D2D2D',
                  transform: `translate(${blackPupil(blackEyeL).x}px, ${blackPupil(blackEyeL).y}px)`,
                  transition: 'transform 0.1s ease-out',
                }"
              />
            </div>
            <div
              ref="blackEyeR"
              class="rounded-full flex items-center justify-center transition-all duration-150"
              :style="{
                width: '16px',
                height: isBlackBlinking ? '2px' : '16px',
                backgroundColor: 'white',
                overflow: 'hidden',
              }"
            >
              <div
                v-if="!isBlackBlinking"
                class="rounded-full"
                :style="{
                  width: '6px',
                  height: '6px',
                  backgroundColor: '#2D2D2D',
                  transform: `translate(${blackPupil(blackEyeR).x}px, ${blackPupil(blackEyeR).y}px)`,
                  transition: 'transform 0.1s ease-out',
                }"
              />
            </div>
          </div>
        </div>

        <!-- 橙色半圆角色 -->
        <div
          ref="orangeRef"
          class="absolute bottom-0 transition-all duration-700 ease-in-out"
          :style="{
            left: '0px',
            width: '240px',
            height: '200px',
            zIndex: 3,
            backgroundColor: '#f59e0b',
            borderRadius: '120px 120px 0 0',
            transform: (props.hasPassword && props.passwordVisible) ? 'skewX(0deg)' : `skewX(${calcBody(orangeRef).bodySkew || 0}deg)`,
            transformOrigin: 'bottom center',
          }"
        >
          <div
            class="absolute flex gap-8 transition-all duration-200 ease-out"
            :style="{
              left: (props.hasPassword && props.passwordVisible) ? '50px' : `${82 + (calcBody(orangeRef).faceX || 0)}px`,
              top: (props.hasPassword && props.passwordVisible) ? '85px' : `${90 + (calcBody(orangeRef).faceY || 0)}px`,
            }"
          >
            <div ref="orangeEyeL" class="rounded-full" :style="{ width: '12px', height: '12px', backgroundColor: '#2D2D2D', transform: `translate(${orangePupil(orangeEyeL).x}px, ${orangePupil(orangeEyeL).y}px)`, transition: 'transform 0.1s ease-out' }" />
            <div ref="orangeEyeR" class="rounded-full" :style="{ width: '12px', height: '12px', backgroundColor: '#2D2D2D', transform: `translate(${orangePupil(orangeEyeR).x}px, ${orangePupil(orangeEyeR).y}px)`, transition: 'transform 0.1s ease-out' }" />
          </div>
        </div>

        <!-- 黄色圆顶角色 -->
        <div
          ref="yellowRef"
          class="absolute bottom-0 transition-all duration-700 ease-in-out"
          :style="{
            left: '310px',
            width: '140px',
            height: '230px',
            backgroundColor: '#E8D754',
            borderRadius: '70px 70px 0 0',
            zIndex: 4,
            transform: (props.hasPassword && props.passwordVisible) ? 'skewX(0deg)' : `skewX(${calcBody(yellowRef).bodySkew || 0}deg)`,
            transformOrigin: 'bottom center',
          }"
        >
          <div
            class="absolute flex gap-6 transition-all duration-200 ease-out"
            :style="{
              left: (props.hasPassword && props.passwordVisible) ? '20px' : `${52 + (calcBody(yellowRef).faceX || 0)}px`,
              top: (props.hasPassword && props.passwordVisible) ? '35px' : `${40 + (calcBody(yellowRef).faceY || 0)}px`,
            }"
          >
            <div ref="yellowEyeL" class="rounded-full" :style="{ width: '12px', height: '12px', backgroundColor: '#2D2D2D', transform: `translate(${yellowPupil(yellowEyeL).x}px, ${yellowPupil(yellowEyeL).y}px)`, transition: 'transform 0.1s ease-out' }" />
            <div ref="yellowEyeR" class="rounded-full" :style="{ width: '12px', height: '12px', backgroundColor: '#2D2D2D', transform: `translate(${yellowPupil(yellowEyeR).x}px, ${yellowPupil(yellowEyeR).y}px)`, transition: 'transform 0.1s ease-out' }" />
          </div>
          <!-- 嘴巴 -->
          <div
            class="absolute w-20 h-1 bg-[#2D2D2D] rounded-full transition-all duration-200 ease-out"
            :style="{
              left: (props.hasPassword && props.passwordVisible) ? '10px' : `${40 + (calcBody(yellowRef).faceX || 0)}px`,
              top: (props.hasPassword && props.passwordVisible) ? '88px' : `${88 + (calcBody(yellowRef).faceY || 0)}px`,
            }"
          />
        </div>

      </div>
    </div>

    <!-- 底部品牌文字 -->
    <div class="absolute bottom-4 left-0 right-0 flex items-center justify-center gap-6 text-xs text-white/30">
      <span>Auto3DQuote</span>
    </div>
  </div>
</template>
