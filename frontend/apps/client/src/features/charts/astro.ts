import { signById } from '../catalog/zodiac'
import { houses } from '../divination/content'

export interface NatalResult {
  house_system: string
  zodiac: string
  ascendant: number
  midheaven: number
  cusps: number[]
  planets: { id: string; name: string; longitude: number; sign: string; house: number; retrograde: boolean }[]
  aspects: { first: string; second: string; name: string; angle: number; orb: number }[]
  utc: string
}

export const birthCities: Record<string, [longitude: number, latitude: number]> = {
  杭州: [120.1551, 30.2741],
  成都: [104.0665, 30.5728],
  北京: [116.4074, 39.9042],
  上海: [121.4737, 31.2304],
  广州: [113.2644, 23.1291],
  深圳: [114.0579, 22.5431],
  南京: [118.7969, 32.0603],
  武汉: [114.3054, 30.5931],
  重庆: [106.5516, 29.5630],
  西安: [108.9398, 34.3416],
  香港: [114.1694, 22.3193],
  台北: [121.5654, 25.0330],
}

export function astroDisplay(result: NatalResult) {
  return result.planets.map((planet) => ({
    planet: planet.name,
    degree: planet.longitude,
    house: planet.house,
    topic: houses[planet.house - 1] || '',
    sign: signById(planet.sign),
    retrograde: planet.retrograde,
    aspect: result.aspects.filter((item) => item.first === planet.id || item.second === planet.id)
      .map((item) => {
        const other = item.first === planet.id ? item.second : item.first
        return item.name + ' ' + (result.planets.find((candidate) => candidate.id === other)?.name || '')
      }).join('、') || '—',
  }))
}
