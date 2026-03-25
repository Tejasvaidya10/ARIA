import Navbar from '@/components/layout/Navbar'
import Hero from '@/components/landing/Hero'
import Features from '@/components/landing/Features'
import Pipeline from '@/components/landing/Pipeline'
import Stats from '@/components/landing/Stats'
import TechStack from '@/components/landing/TechStack'
import Architecture from '@/components/landing/Architecture'
import CallToAction from '@/components/landing/CallToAction'
import Footer from '@/components/landing/Footer'

export default function LandingPage() {
  return (
    <div className="bg-dark-900 text-white antialiased">
      <Navbar />
      <Hero />
      <Features />
      <Pipeline />
      <Stats />
      <TechStack />
      <Architecture />
      <CallToAction />
      <Footer />
    </div>
  )
}
