<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="aside">
      <div class="header-title">算法测试平台</div>
      <el-menu
        :default-active="$route.path"
        background-color="#001529"
        text-color="#dcdfe6"
        active-text-color="#409EFF"
        router
      >
        <el-sub-menu index="asr">
          <template #title>
            <el-icon><Microphone /></el-icon>
            <span>ASR</span>
          </template>
          <el-menu-item index="/asr/models">模型管理</el-menu-item>
          <el-menu-item index="/asr/datasets">数据集管理</el-menu-item>
          <el-menu-item index="/asr/pool">数据池</el-menu-item>
          <el-menu-item index="/asr/tasks">测试任务管理</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/mt">
          <el-icon><Document /></el-icon>
          <span>MT</span>
        </el-menu-item>
        <el-menu-item index="/tts">
          <el-icon><VideoPlay /></el-icon>
          <span>TTS</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background:#fff;display:flex;align-items:center;border-bottom:1px solid #eee;">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>{{ $route.meta?.title || '' }}</el-breadcrumb-item>
        </el-breadcrumb>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { Microphone, Document, VideoPlay } from '@element-plus/icons-vue'
</script>
