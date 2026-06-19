import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    userId: null,
    userName: '',
    nickName: '',
    headImageThumb: '',
  }),
  actions: {
    setUserInfo(payload) {
      if (payload.userId !== undefined) this.userId = payload.userId
      if (payload.userName !== undefined) this.userName = payload.userName
      if (payload.nickName !== undefined) this.nickName = payload.nickName
      if (payload.headImageThumb !== undefined) this.headImageThumb = payload.headImageThumb
    },
    clear() {
      this.userId = null
      this.userName = ''
      this.nickName = ''
      this.headImageThumb = ''
    },
  },
})

export default useUserStore
