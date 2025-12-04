import { translations } from '~/locales/ru'

type TranslationKey = string

/**
 * Simple translation function
 * Usage: t('common.loading') or t('profile.title')
 */
export const useI18n = () => {
  const t = (key: TranslationKey): string => {
    const keys = key.split('.')
    let value: any = translations
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k as keyof typeof value]
      } else {
        // Return key if translation not found
        console.warn(`Translation key not found: ${key}`)
        return key
      }
    }
    
    return typeof value === 'string' ? value : key
  }
  
  return { t }
}
