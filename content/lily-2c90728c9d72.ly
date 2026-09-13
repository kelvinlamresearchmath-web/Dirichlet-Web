
  \relative bes'' {
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
    \clef "treble" \time 3/4 \key bes \major \transposition bes
    \acciaccatura bes,8 bes'2( a8 g8 |
    f4. e8 es8 c8 |
    bes4.. a16 bes8. c16) |
    d2( c8) r8 |
    \bar "||"
  }
