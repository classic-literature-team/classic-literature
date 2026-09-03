import '@/styles/home.css'

import { useState } from 'react'

import { ArranPanel } from '@/components/home/ArranPanel'
import { GenrePanel, GraphPanel } from '@/components/home/GraphGenrePanels'
import {
  Hero,
  MainNav,
  Sidebar,
  StatsStrip,
} from '@/components/home/HomeSections'
import {
  BiblioPanel,
  ExprePanel,
  IntroPanel,
  PartiPanel,
} from '@/components/home/StaticPanels'
import { YangsPanel } from '@/components/home/YangsPanel'
import { type TabId } from '@/data/home-content'

const panels: Record<TabId, React.ReactNode> = {
  intro: <IntroPanel />,
  biblio: <BiblioPanel />,
  parti: <PartiPanel />,
  arran: <ArranPanel />,
  expre: <ExprePanel />,
  graph: <GraphPanel />,
  genre: <GenrePanel />,
  yangs: <YangsPanel />,
}

export function HomePage() {
  const [activeTab, setActiveTab] = useState<TabId>('intro')

  return (
    <div className="home-root">
      <Hero />
      <MainNav active={activeTab} onSelect={setActiveTab} />
      <StatsStrip />

      <main className="content-wrap">
        <div className="panels-area">
          <div className="panel visible" key={activeTab}>
            {panels[activeTab]}
          </div>
        </div>
        <Sidebar />
      </main>

      <footer className="site-footer">
        <p>Produced by Lee Gil-Hwan</p>
      </footer>
    </div>
  )
}
