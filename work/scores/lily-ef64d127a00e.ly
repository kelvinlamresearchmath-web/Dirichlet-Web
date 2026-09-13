\version "2.24.4"
\pointAndClickOff
\header { tagline = ##f }
\paper { indent = 0\mm line-width = 160\mm ragged-right = ##t }
\score { {

    \override Staff.StaffSymbol.color       = #white
    \override Staff.Clef.color              = #white
    \override Staff.TimeSignature.color     = #white
    \override Staff.KeySignature.color      = #white
    \override Staff.BarLine.color           = #white
    \override Staff.LedgerLineSpanner.color = #white
    \override NoteHead.color                = #white
    \override Stem.color                    = #white
    \override Beam.color                    = #white
    \override Flag.color                    = #white
    \override Rest.color                    = #white
    \override Accidental.color              = #white
    \override Dots.color                    = #white
    \override Slur.color                    = #white
    \override Tie.color                     = #white
    \override Script.color                  = #white
    \override DynamicText.color             = #white
    \override Hairpin.color                 = #white
    \override TextScript.color              = #white
    \override TupletBracket.color           = #white
    \override TupletNumber.color            = #white
  \clef treble
  \key g \major
  \time 12/8
\relative c' {
g''4.( fis4) dis8 fis4( e8) d4( b8) d4( c8) a4( fis8) fis4.( fis8)( g a)
} \bar "||"

} \layout { } }
