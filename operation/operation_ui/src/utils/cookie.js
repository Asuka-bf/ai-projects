/**
 * Cookie 读写
 */
const defaultDays = 7

function setExpires(days) {
  const date = new Date()
  date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000)
  return date.toUTCString()
}

export function getCookie(name) {
  const key = name + '='
  const list = document.cookie.split(';')
  for (let i = 0; i < list.length; i++) {
    let item = list[i]
    while (item.charAt(0) === ' ') {
      item = item.substring(1)
    }
    if (item.indexOf(key) === 0) {
      return decodeURIComponent(item.substring(key.length))
    }
  }
  return ''
}

export function setCookie(name, value, days = defaultDays) {
  const expires = days < 0 ? 'Thu, 01 Jan 1970 00:00:00 GMT' : setExpires(days)
  document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires};path=/`
}

export default {
  getCookie,
  setCookie,
}
