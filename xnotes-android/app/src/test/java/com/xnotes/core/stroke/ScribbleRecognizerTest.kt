package com.xnotes.core.stroke

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ScribbleRecognizerTest {
    @Test fun straightStrokeIsNotAScribble() {
        val samples = (0..20).map { Sample(it * 5.0, 0.0, 1.0) }
        assertFalse(ScribbleRecognizer.isScribble(samples))
    }

    @Test fun selfCrossingStrokeIsAScribble() {
        val samples = listOf(
            Sample(0.0, 0.0, 1.0),
            Sample(60.0, 60.0, 1.0),
            Sample(120.0, 0.0, 1.0),
            Sample(60.0, 60.0, 1.0),
            Sample(0.0, 0.0, 1.0),
            Sample(60.0, 60.0, 1.0),
            Sample(120.0, 0.0, 1.0),
            Sample(60.0, 60.0, 1.0),
            Sample(0.0, 0.0, 1.0),
            Sample(60.0, 60.0, 1.0),
            Sample(120.0, 0.0, 1.0),
            Sample(60.0, 60.0, 1.0),
        )
        assertTrue(ScribbleRecognizer.isScribble(samples))
    }

    @Test fun shortGestureIsNotAScribble() {
        val samples = (0..20).map { Sample(it * 1.0, 0.0, 1.0) }
        assertFalse(ScribbleRecognizer.isScribble(samples))
    }
}
