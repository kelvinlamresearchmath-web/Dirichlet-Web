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
  \relative bes'' {
  \clef "treble"
  \time 2/4
  \key g \major
  \transposition bes
  g,,16 -.  a16 -. b16 -. c16 -. d16 -. e16 -. fis16 -. g16 -.
    a16 -. b16 -. c16 -. d16 -. e16 -. fis16 -. g16 -. a16 -.
    b8 -.  b8 -. \acciaccatura { b8 ( } a16 ) g16 a16 b16 g8 -.
    b8 -. g8 r8 \bar "||"}

} \layout { } }
