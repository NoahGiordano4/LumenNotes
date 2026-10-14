package com.xnotes.core.stroke

import kotlin.math.abs
import kotlin.math.max

/** Detects the deliberately messy, self-crossing gesture used to erase ink. */
object ScribbleRecognizer {
    private const val MIN_SAMPLES = 12
    private const val MIN_LENGTH = 48.0
    private const val MIN_TURNS = 2

    fun isScribble(samples: List<Sample>): Boolean {
        if (samples.size < MIN_SAMPLES) return false
        val first = samples.first()
        var minX = first.x
        var maxX = first.x
        var minY = first.y
        var maxY = first.y
        var length = 0.0
        var turns = 0
        var previousTurn = 0

        for (i in 1 until samples.size) {
            val previous = samples[i - 1]
            val current = samples[i]
            val dx = current.x - previous.x
            val dy = current.y - previous.y
            length += abs(dx) + abs(dy)
            minX = minOf(minX, current.x)
            maxX = maxOf(maxX, current.x)
            minY = minOf(minY, current.y)
            maxY = maxOf(maxY, current.y)
            if (i < samples.lastIndex) {
                val next = samples[i + 1]
                val cross = dx * (next.y - current.y) - dy * (next.x - current.x)
                val turn = when {
                    cross > 1e-6 -> 1
                    cross < -1e-6 -> -1
                    else -> 0
                }
                if (turn != 0 && previousTurn != 0 && turn != previousTurn) turns++
                if (turn != 0) previousTurn = turn
            }
        }

        val width = maxX - minX
        val height = maxY - minY
        val span = max(width, height)
        if (span < MIN_LENGTH || length < span * 2.5) return false
        return turns >= MIN_TURNS || hasSelfIntersection(samples)
    }

    private fun hasSelfIntersection(samples: List<Sample>): Boolean {
        for (i in 1 until samples.size) {
            val a = samples[i - 1]
            val b = samples[i]
            for (j in 1 until i - 2) {
                val c = samples[j - 1]
                val d = samples[j]
                if (segmentsIntersect(a, b, c, d)) return true
            }
        }
        return false
    }

    private fun segmentsIntersect(a: Sample, b: Sample, c: Sample, d: Sample): Boolean {
        fun orientation(p: Sample, q: Sample, r: Sample): Double =
            (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)

        val abC = orientation(a, b, c)
        val abD = orientation(a, b, d)
        val cdA = orientation(c, d, a)
        val cdB = orientation(c, d, b)
        return (abC > 0.0) != (abD > 0.0) && (cdA > 0.0) != (cdB > 0.0)
    }
}
