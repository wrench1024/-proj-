<template>
  <div class="loading">
    <!--  三个黑点 -->
    <div></div>
    <div></div>
    <div></div>
  </div>
</template>

<style lang="scss" scoped>
  .loading {
    display: flex;
    justify-content: space-around;
    color: #000;
    width: 54px;
    padding: 15px;

    div {
      background-color: currentColor;
      border: 0 solid currentColor;
      width: 5px;
      height: 5px;
      border-radius: 100%;
      animation: ball-beat 0.7s -0.15s infinite linear;
    }

    div:nth-child(2n-1) {
      animation-delay: -0.5s;
    }
  }

  @keyframes ball-beat {
    50% {
      opacity: 0.2;
      transform: scale(0.75);
    }
    100% {
      opacity: 1;
      transform: scale(1);
    }
  }
</style>