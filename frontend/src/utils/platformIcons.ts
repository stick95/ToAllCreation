/**
 * Platform Icons Utility
 * Centralized mapping of social media platform icons
 */
import facebookIcon from '../assets/icons/facebook.svg'
import instagramIcon from '../assets/icons/instagram.png'
import twitterIcon from '../assets/icons/twitter.svg'
import youtubeIcon from '../assets/icons/youtube.svg'
import linkedinIcon from '../assets/icons/linkedin.png'
import tiktokIcon from '../assets/icons/tiktok.svg'

export const PLATFORM_ICONS: Record<string, string> = {
  facebook: facebookIcon,
  instagram: instagramIcon,
  twitter: twitterIcon,
  youtube: youtubeIcon,
  linkedin: linkedinIcon,
  tiktok: tiktokIcon
}

export const getPlatformIcon = (platform: string): string => {
  return PLATFORM_ICONS[platform.toLowerCase()] || ''
}
