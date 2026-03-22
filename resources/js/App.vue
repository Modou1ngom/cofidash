<template>
  <router-view />
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  width: 100%;
  min-height: 100%;
  overflow-x: hidden;
}

body {
  width: 100%;
  min-height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  overflow-x: hidden;
}

#app {
  width: 100%;
  min-height: 100vh;
}

.page-adapt {
  width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

/* Sections du Dashboard - adaptation à l'écran */
.main-content > * {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}
</style>

