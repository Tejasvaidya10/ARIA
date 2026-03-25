export default function Logo({ className = 'h-8', variant = 'icon' }) {
  const src = variant === 'hero' ? '/aria-hero.png' : '/aria-navbar.png'
  return (
    <img src={src} alt="ARIA" className={className} />
  )
}
