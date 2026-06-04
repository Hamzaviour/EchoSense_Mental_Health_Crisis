import { Wind, Footprints, Moon, Shield, Headphones } from 'lucide-react'
import AppLayout from '@/components/layout/AppLayout'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useLanguage } from '@/context/LanguageContext'
import BreathingExercise from '@/components/patient/coping/BreathingExercise'
import GroundingExercise from '@/components/patient/coping/GroundingExercise'
import SleepGuidance from '@/components/patient/coping/SleepGuidance'
import AnxietyRelief from '@/components/patient/coping/AnxietyRelief'
import MindfulnessSession from '@/components/patient/coping/MindfulnessSession'

export default function CopingTools() {
  const { t } = useLanguage()

  const toolCards = [
    { id: 'breathing', icon: Wind, title: t.coping.breathing, desc: t.coping.breathingDesc },
    { id: 'grounding', icon: Footprints, title: t.coping.grounding, desc: t.coping.groundingDesc },
    { id: 'sleep', icon: Moon, title: t.coping.sleep, desc: t.coping.sleepDesc },
    { id: 'anxiety', icon: Shield, title: t.coping.anxiety, desc: t.coping.anxietyDesc },
    { id: 'mindfulness', icon: Headphones, title: t.coping.mindfulness, desc: t.coping.mindfulnessDesc },
  ]

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl w-full flex-1 flex flex-col p-4 md:p-6 gap-6">
        <div>
          <h1 className="text-2xl font-semibold text-calm-900">{t.coping.title}</h1>
          <p className="text-muted-foreground mt-1">{t.coping.subtitle}</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {toolCards.map(({ id, icon: Icon, title, desc }) => (
            <Card key={id} className="border-calm-100/80">
              <CardHeader className="p-4">
                <Icon className="h-5 w-5 text-primary mb-2" />
                <CardTitle className="text-sm">{title}</CardTitle>
                <CardDescription className="text-xs">{desc}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>

        <Tabs defaultValue="breathing" className="flex-1">
          <TabsList className="flex flex-wrap h-auto gap-1">
            {toolCards.map(({ id, title }) => (
              <TabsTrigger key={id} value={id} className="text-xs sm:text-sm">
                {title}
              </TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value="breathing"><BreathingExercise /></TabsContent>
          <TabsContent value="grounding"><GroundingExercise /></TabsContent>
          <TabsContent value="sleep"><SleepGuidance /></TabsContent>
          <TabsContent value="anxiety"><AnxietyRelief /></TabsContent>
          <TabsContent value="mindfulness"><MindfulnessSession /></TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  )
}
