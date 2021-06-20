---
author:
- Mohammed Asir Shahid
date: '2021-05-15'
title: Lec 1 Probability Models And Axioms
---

1. Motivation {#sec:org66f124c}
=============

We need to be able to make decisions under uncertainty {#sec:org4d31840}
------------------------------------------------------

2. Lecture 1 overview and slides {#sec:org178cf39}
================================

Downloaded PDF for lecture slides {#sec:orge5fc4d0}
---------------------------------

3. Sample space {#sec:orgd6394fd}
===============

Two Steps: {#sec:org7318679}
----------

### Describe possible outcomes {#sec:org04cc902}

### Describe beliefs about likelihood {#sec:org50a5ef9}

List set of possible outcomes $\Omega$ {#sec:orgffd9c6c}
--------------------------------------

The elements out our set should have some properties {#sec:org9e1d51f}
----------------------------------------------------

### Mutually exclusive {#sec:orgeb72d47}

1.  If one outcome happened, others can not happen
    [\[sec:org80ac1cd\]]{#sec:org80ac1cd label="sec:org80ac1cd"}

### Collectively exhaustive {#sec:orgc035f8b}

1.  All the elements of the set make up all possibilities
    [\[sec:orgafe132f\]]{#sec:orgafe132f label="sec:orgafe132f"}

### At the right granularity {#sec:org146988f}

Ex. {#sec:org09f2e7f}
---

### Flipping a coin. Our outcomes are heads or tails. {#sec:org45a784e}

1.  Let's say we also looked outside while flipping the coin.
    [\[sec:org39018db\]]{#sec:org39018db label="sec:org39018db"}

    1.  Either it's heads and rain, heads and no rain, tails and rain,
        or tails and no rain. [\[sec:org5f341cf\]]{#sec:org5f341cf
        label="sec:org5f341cf"}

        1.  This is also a valid sample space.
            [\[sec:orgc09a553\]]{#sec:orgc09a553 label="sec:orgc09a553"}

        2.  However, since we are just curious about whether its heads
            or tails, this second sample space isn't as relevant.
            [\[sec:org0f0a07d\]]{#sec:org0f0a07d label="sec:org0f0a07d"}

4. Exercise: Sample space {#sec:org2f17348}
=========================

For the experiment of flipping a coin, and for each one of the following choices, determine whether we have a legitimate sample space: {#sec:org3371012}
--------------------------------------------------------------------------------------------------------------------------------------

\$$\Omega$\$={Heads and it is raining, Heads and it is not raining, Tails} {#sec:orgf2001b9}
--------------------------------------------------------------------------

### Yes {#sec:orgbad0e75}

\$\$P(A$\cup$ B$\Omega$\$={Heads and it is raining, Tails and it is not raining, Tails} {#sec:org0e6655e}
---------------------------------------------------------------------------------------

### No {#sec:orgd630e9e}

5. Sample space examples {#sec:orge5ea451}
========================

Discrete/finite example {#sec:org0163a4b}
-----------------------

### Two rolls of a tetrahedral die {#sec:org828bfd1}

1.  We have pairs of numbers. One containing the result of the first die
    and another containing the result of hte second die.
    [\[sec:org748774c\]]{#sec:org748774c label="sec:org748774c"}

    1.  Result could be written as (1,1) if first die was 1 and second
        die was 1, (1,2) if first die was 1 and second die was 2, etc.
        [\[sec:org2966f2b\]]{#sec:org2966f2b label="sec:org2966f2b"}

2.  Sequential description- [\[sec:orgfbe0fe6\]]{#sec:orgfbe0fe6
    label="sec:orgfbe0fe6"}

    1.  An experiment with several stages such as this can be described
        as a tree [\[sec:org226ed4f\]]{#sec:org226ed4f
        label="sec:org226ed4f"} <https://i.imgur.com/k6Hl4NP.png>

    2.  This shows us a distinction in the stages, with 16 different
        outcomes. [\[sec:orgd1fc6d9\]]{#sec:orgd1fc6d9
        label="sec:orgd1fc6d9"}

Continuous example {#sec:org058f57d}
------------------

### If we have a dart board, where we are throwing darts with X and Y axis, we can record the coordinates as real numbers with infinite precision. This gives us an infinite amount of possibilities for our sample space, thus we have a continuous sample space. {#sec:orgcced99f}

6. Exercise: Tree representations {#sec:org0fd695c}
=================================

Paul checks the weather forecast. If the forecast is good, Paul will go out for a walk. If the forecast is bad, then Paul will either stay home or go out. If he goes out, he might either remember or forget his umbrella. In the tree diagram below, identify the leaf that corresponds to the event that the forecast is bad and Paul stays home. {#sec:org1cde13d}
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

<https://courses.edx.org/assets/courseware/v1/641ba94a18d06ac5698cf9a413c42bd2/asset-v1:MITx+6.431x+2T2021+type@asset+block/images_texshop_image.jpg>

### 1 Represents the forecast being good, as the decision making ends there. Paul will definitely go for a walk. {#sec:org13fdc9a}

### If the forecast is bad, we have choices to make. 2 represents the weather being good and Paul deciding to stay home. {#sec:org115612b}

### If the forecast is bad, Paul could still go out. In which case he could either remember or forget his umbrella which would be 3 and 4. {#sec:orgd3aa948}

7. Probability axioms {#sec:org31ade46}
=====================

Now we can see how to figure out which occurences are more/less likely to occur. {#sec:org8303eba}
--------------------------------------------------------------------------------

However, we have an issue when it comes to continuous sample spaces. {#sec:orgdeeac16}
--------------------------------------------------------------------

### The probability of hitting any single point on a continuous space is essentially 0. {#sec:org6639f2e}

Event: A subset of the sample space. {#sec:org1866f0a}
------------------------------------

### We will instead assign probability to events. {#sec:org6c2db7b}

1.  $P(A)$ [\[sec:org9ca6b03\]]{#sec:org9ca6b03 label="sec:org9ca6b03"}

2.  So even though individual events have 0 probablity, these events
    have some probability. [\[sec:orgf9183ad\]]{#sec:orgf9183ad
    label="sec:orgf9183ad"}

Axioms: {#sec:orge23a5ae}
-------

### Nonnegativity: $P(A)\ge 0$ {#sec:orgf54790e}

### Normalization: $P(\Omega)=1$ {#sec:org56c0686}

1.  The probability of our sample space occuring is 1.
    [\[sec:orgbf37b43\]]{#sec:orgbf37b43 label="sec:orgbf37b43"}

### Finite Additivity: {#sec:org3b67d0b}

If $A \cap B = \varnothing$, then $P(A \cup B)=P(A)+P(B)$

1.  When the intersection between A and B is the empty set, then they
    are considered disjoint. Then $P(A\cup B)=P(A)+P(B)$
    [\[sec:orgc7f0150\]]{#sec:orgc7f0150 label="sec:orgc7f0150"}

    1.  This is due to the fact that there is no overlap in $P(A)$ or
        $P(B)$. [\[sec:org0a9e0cd\]]{#sec:org0a9e0cd
        label="sec:org0a9e0cd"}

2.  This axiom needs to be refined and strengthened later.
    [\[sec:org6369478\]]{#sec:org6369478 label="sec:org6369478"}

### These axioms are the only ones that need to be stated. Anything else, such as $P(A)\leq 1$ is already implied from our axioms. {#sec:org6ce1b93}

8. Exercise: Axioms {#sec:orgb57e900}
===================

Let A and B be events on the same sample space, with P(A)=0.6 and P(B)=0.7. Can these two events be disjoint? {#sec:org940ee92}
-------------------------------------------------------------------------------------------------------------

### No because $P(A)+P(B)>1$. If they were disjoint, then $P(A)+P(B)=P(A\cup B)=1.3$ which is greater than 1. This would contradict the normalization axiom {#sec:orgc26d6e7}

9. Simple properties of probabilities {#sec:orga327be0}
=====================================

Consequences of axioms: {#sec:org0d62d97}
-----------------------

### (A) $P(A)\ge 0$ implies that $P(A)\le 1$ {#sec:org22900d3}

### (B) $P(\Omega)=1$ implies that $P(\varnothing)=0$ {#sec:orge4d3628}

### (C) $P(A\cup B)=P(A)+P(B)$ implies that $P(A)+P(A^c)=1$ and that $P(A\cup B\cup C)=P(A)+P(B)+P(C)$ for $k$ disjoint sets. {#sec:orgb2397a3}

1.  An element and its compliment makes up $\Omega$ and the intersection
    of a set and its compliment is $\varnothing$.
    [\[sec:org0b6733b\]]{#sec:org0b6733b label="sec:org0b6733b"}

2.  From (B), $P(\Omega)=1$ which is equal to $P(A\cup A^c)$. This is
    equal to $P(A)+P(A^c)$. [\[sec:orgc8cb3c9\]]{#sec:orgc8cb3c9
    label="sec:orgc8cb3c9"}

    1.  Based on this, we can write that $P(A)=1-P(A^c)\le 1$.
        [\[sec:orgf683756\]]{#sec:orgf683756 label="sec:orgf683756"}

3.  $1=P(\Omega)+P(\Omega^c)$ [\[sec:orgc2fc87a\]]{#sec:orgc2fc87a
    label="sec:orgc2fc87a"}

    1.  $1=1+P(\Omega^c) \Rightarrow 1=1+P(\varnothing)\Rightarrow P(\varnothing)=0$
        [\[sec:org9ada5be\]]{#sec:org9ada5be label="sec:org9ada5be"}

4.  When $A,B,C$ are disjoint, $P(A\cup B\cup C)=P(A)+P(B)+P(C)$.
    [\[sec:org1445614\]]{#sec:org1445614 label="sec:org1445614"}

    1.  We can think of the $P(A\cup B\cup C)$ as
        $P((A\cup B)\cup C)=P(A\cup B)+P(C)=P(A)+P(B)+P(C)$
        [\[sec:org10fd1b4\]]{#sec:org10fd1b4 label="sec:org10fd1b4"}

        1.  This logic can be continued for $k$ disjoint sets. Can prove
            by induction. [\[sec:orgdd5f51a\]]{#sec:orgdd5f51a
            label="sec:orgdd5f51a"}

        2.  If $(A_1,\cdots ,A_k)$ then
            $P(A_1\cup \cdots \cup A_k = \sum_{i=1}^{k}P(A_i)$
            [\[sec:org712cf12\]]{#sec:org712cf12 label="sec:org712cf12"}

5.  $P(\{s_1,s_2,\cdots,s_k\}) = P(\{s_1\}\cup\cdots \cup \{s_k\}) = P(\{s_1\})+\cdots + P(\{s_k\})=P(s_1)+\cdots + P(s_k)$
    [\[sec:org9e596f5\]]{#sec:org9e596f5 label="sec:org9e596f5"}

10. Exercise: Simple properties {#sec:org7683a7e}
===============================

Let A, B, and C be disjoint subsets of the sample space. For each one of the following statements, determine whether it is true or false. Note: "False" means "not guaranteed to be true. {#sec:org38b2e84}
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### $P(A)+P(A^c)+P(B)=P(A\cup A^c\cup B)$ {#sec:org0638beb}

1.  This statement is false. While A and the compliment of A are known
    to be disjoint, we do not know if this also applies to A and B or
    $A^c$ and B. [\[sec:orgf70fe11\]]{#sec:orgf70fe11
    label="sec:orgf70fe11"}

### $P(A)+P(B)\le 1$ {#sec:orgcdff96b}

1.  This statement is true since A and B are disjoint,
    $P(A)+P(B)=P(A\cup B)$ which can not be greater than 1.
    [\[sec:org226c94f\]]{#sec:org226c94f label="sec:org226c94f"}

### $P(A^c)+P(B)\le 1$ {#sec:org19a2beb}

1.  This is false. For example, consider A situation where
    $A=\varnothing$. Then $A^c=\Omega$. Now given that A and B are
    disjoint, no matter what B is, $P(\Omega)+P(B)>1$.
    [\[sec:orgddd56b0\]]{#sec:orgddd56b0 label="sec:orgddd56b0"}

### $P(A\cup B\cup C)\ge P(A\cup B)$. {#sec:orge25889f}

1.  This must be true. Given that these are disjoint, we know that
    $P(A\cup B\cup C)=P(A)+P(B)+P(C)$. And we also know that
    $P(A\cup B)= P(A)+P(B)$. So given that the probability of an event
    must be nonnegative, we know $P(A\cup B\cup C)$ must be greater than
    or equal to $P(A\cup B)$. [\[sec:orgf534d65\]]{#sec:orgf534d65
    label="sec:orgf534d65"}

11. More properties of probabilities {#sec:org69aa9c4}
====================================

More consequences of axioms: {#sec:org62f89cb}
----------------------------

### If $A \subset B$, then $P(A)\le P(B)$ {#sec:orgba2532a}

1.  This seems obvious, but how can we prove this?
    [\[sec:org3a4ee23\]]{#sec:org3a4ee23 label="sec:org3a4ee23"}

    1.  $B$ can be written as $A \cup (B \cap A^c)$.
        [\[sec:org64c3819\]]{#sec:org64c3819 label="sec:org64c3819"}

    2.  Thus $P(B)=P(A) +P(B \cap A^c)\ge P(A)$
        [\[sec:org4af2d45\]]{#sec:org4af2d45 label="sec:org4af2d45"}

    3.  So since probabilities are nonnegative, we know that
        $P(A) \le P(B)$ [\[sec:orgfba0c1e\]]{#sec:orgfba0c1e
        label="sec:orgfba0c1e"}

### $P(A \cup B) = P(A) + P(B) -P(A \cap B)$ even if these sets are not disjoint. {#sec:orgde3017a}

1.  The union of A and B can be broken down into 3 distinct parts.
    [\[sec:org398c7fc\]]{#sec:org398c7fc label="sec:org398c7fc"}

    1.  $a=P(A \cap B^c)$ [\[sec:org5e3026f\]]{#sec:org5e3026f
        label="sec:org5e3026f"}

    2.  $b=P(A \cap B)$ [\[sec:org8ef05bb\]]{#sec:org8ef05bb
        label="sec:org8ef05bb"}

    3.  $c=P(B  \cap A^c)$ [\[sec:org142ed77\]]{#sec:org142ed77
        label="sec:org142ed77"}

2.  Then $P(A \cup B) =a+b+c$ [\[sec:org16bcbdc\]]{#sec:org16bcbdc
    label="sec:org16bcbdc"}

    1.  $P(A)+P(B)-P(A\cap B)=(a+b)+(b+c)-b=a+b+c$
        [\[sec:org72dacf5\]]{#sec:org72dacf5 label="sec:org72dacf5"}

    2.  Thus we can see that this is true.
        [\[sec:orga903ba9\]]{#sec:orga903ba9 label="sec:orga903ba9"}

3.  This leads us to the following union bound:
    [\[sec:org4e7fe52\]]{#sec:org4e7fe52 label="sec:org4e7fe52"}

### $P(A \cup B) \le P(A) + P(B)$ {#sec:org50a6c8e}

1.  This is called the union bound and can be used when proving the
    probability of something is less than the probability of something
    else. [\[sec:org06214ad\]]{#sec:org06214ad label="sec:org06214ad"}

2.  $P(A \cup B \cup C) = P(A) +P(A^c \cap B) + P(A^c \cap B^c \cap C)$
    [\[sec:org53f10d9\]]{#sec:org53f10d9 label="sec:org53f10d9"}

    1.  We have several pieces: [\[sec:org75f254c\]]{#sec:org75f254c
        label="sec:org75f254c"}

        1.  $A \cup B \cup C=A \cup (B \cap A^c) \cup (C \cap A^c \cap B^c)$
            [\[sec:orgc306eec\]]{#sec:orgc306eec label="sec:orgc306eec"}

    2.  These three pieces are disjoint, thus the additivity axiom gives
        us: [\[sec:orge1b4b1b\]]{#sec:orge1b4b1b label="sec:orge1b4b1b"}

        1.  $P(A \cup B \cup C)=P(A)+ P(\cup (B \cap A^c)) + P(C \cap A^c \cap B^c)$
            [\[sec:org404f299\]]{#sec:org404f299 label="sec:org404f299"}

12. Exercise: More properties {#sec:org7657ce4}
=============================

Let A, B, and C be subsets of the sample space, not necessarily disjoint. For each one of the following statements, determine whether it is true or false. Note: "False" means "not guaranteed to be true." {#sec:orgef69561}
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### $P( (A \cap B) \cup (C \cap A^c) ) \le P(A \cup B \cup C)$ {#sec:org849098d}

1.  This statement must be true. This is due to the fact that $A \cap B$
    cannot be any bigger than $A \cup B$ and $C \cap A^c$ cannot be any
    bigger than $C$. Thus this statement is true.
    [\[sec:org29d9c56\]]{#sec:org29d9c56 label="sec:org29d9c56"}

### $P( A \cup B \cup C ) = P( A \cap C^c ) + P(C) + P( B \cap A^c \cap C^c )$ {#sec:orga5c97d1}

1.  This statement must be true. It is the same property we saw earlier
    in 11. [\[sec:org274d8a6\]]{#sec:org274d8a6 label="sec:org274d8a6"}

13. A discrete example {#sec:orgd88b521}
======================

We can move from the abstract to the concrete. {#sec:org33ce633}
----------------------------------------------

When we have two rolls of a tetrahedral dice, we have 16 possible outcomes, all of which are equally likely. {#sec:org3017d18}
------------------------------------------------------------------------------------------------------------

$P(X=1) = \frac{1}{4}$ {#sec:orgc51971e}
----------------------

### Where X is the value of the first roll. {#sec:orgcefcda6}

Let $Z=\min(X,Y)$ {#sec:orgbbd2a53}
-----------------

### $P(Z=4)= \frac{1}{16}$ {#sec:org02516aa}

### $P(Z=2) = \frac{1}{16} + \frac{2}{16} + \frac{2}{16} = \frac{5}{16}$ {#sec:org148fd9a}

This example is something called a Discrete Uniform Law. {#sec:org4a104e5}
--------------------------------------------------------

### Assume $\Omega$ consists of $n$ equally likely elements {#sec:orgf743549}

### Assume $A$ consists of $k$ elements {#sec:org3b62179}

### $P(A) = k*\frac{1}{n}$ {#sec:org69c0cc6}

14. Exercise: Discrete probability calculations {#sec:org2a42a63}
===============================================

Consider the same model of two rolls of a tetrahedral die, with all 16 outcomes equally likely. Find the probability of the following events: {#sec:orgddb2aaf}
---------------------------------------------------------------------------------------------------------------------------------------------

### The value in the first roll is strictly larger than the value in the second roll. {#sec:org820bd8c}

1.  This event contains the times the first roll is strictly larger than
    the second. The first will be equal to the second a fourth of the
    time. The two rolls are not equal $\frac{3}{4}$ of the time, which
    in this case means 12 of the 16 rolls will not be equal. In half of
    these occurences, the first roll will be greater than the second
    roll, and vice versa in the other half. Thus, we have a
    $\frac{6}{16}$ probability that the first roll will be strictly
    greater than the second. [\[sec:orgd725fb5\]]{#sec:orgd725fb5
    label="sec:orgd725fb5"}

### The sum of the values obtained in the two rolls is an even number. {#sec:orgd83d20a}

1.  This event will happen half the time, since half our numbers are
    even numbers and half are odd. So the probability will be
    $\frac{8}{16}$ [\[sec:org474e4d0\]]{#sec:org474e4d0
    label="sec:org474e4d0"}

15. A continuous example {#sec:orgaab2a89}
========================

Probability calculation: Continuous example {#sec:org4066f05}
-------------------------------------------

### $\left( x,y \right)$ such that $0 \le x,y \le 1$ {#sec:org341f14b}

1.  We need to specify a uniform probability law
    [\[sec:org1e90e5b\]]{#sec:org1e90e5b label="sec:org1e90e5b"}

    1.  Meaning, the probability is equal to the area.
        [\[sec:org96f3989\]]{#sec:org96f3989 label="sec:org96f3989"}

    2.  $P( \{\left( x,y \right) | x+y \le \frac{1}{2} \} )$
        [\[sec:orgce6ffb6\]]{#sec:orgce6ffb6 label="sec:orgce6ffb6"}

        1.  These points form a triangle between the line
            $x+y=\frac{1}{2}$ [\[sec:orge943757\]]{#sec:orge943757
            label="sec:orge943757"}

        2.  So the probability is equal to the area of the triangle
            which is
            $\frac{1}{2} * \frac{1}{2} * \frac{1}{2} = \frac{1}{8}$
            [\[sec:org8328f73\]]{#sec:org8328f73 label="sec:org8328f73"}

    3.  $P(\{\left( 0.5,0.3 \right)\})$
        [\[sec:org730bca6\]]{#sec:org730bca6 label="sec:org730bca6"}

        1.  This event consists of only one element, a single point.
            [\[sec:orgc05b44e\]]{#sec:orgc05b44e label="sec:orgc05b44e"}

        2.  The area of a single point is 0, so the probability of
            having this single point, or any other single point, is
            simply 0. [\[sec:orgd76ced4\]]{#sec:orgd76ced4
            label="sec:orgd76ced4"}

Probability calculation steps {#sec:org7d7ef1f}
-----------------------------

### Specify the sample space {#sec:org39db1ea}

### Specify a probability law {#sec:org6c6305b}

### Identify an event of interest {#sec:orgeaa6241}

### Calculate {#sec:orgd4ac1ff}

16. Exercise: Continuous probability calculations {#sec:org96c9a14}
=================================================

Consider a sample space that is the rectangular region \[0,1\]×\[0,2\], i.e., the set of all pairs (x,y) that satisfy 0≤x≤1 and 0≤y≤2. Consider a "uniform" probability law, under which the probability of an event is half of the area of the event. Find the probability of the following events: {#sec:org0803448}
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### The two components x and y have the same values {#sec:org61a5499}

1.  This event is simply a line, which has no area. Thus the probability
    of this will be $0$. [\[sec:orgec085fa\]]{#sec:orgec085fa
    label="sec:orgec085fa"}

### The value, x, of the first component is larger than or equal to the value, y, of the second component. {#sec:orgd48a526}

1.  This would make up a triangle with points at $(0,1),(1,0),(1,1)$.
    The area of such a triangle is 0.5 and the total area of the region
    is 2. Thus the probability of the x value being larger than the y
    value is $\frac{1}{4}$ [\[sec:org62d089d\]]{#sec:org62d089d
    label="sec:org62d089d"}

### The value of x^2^ is larger than or equal to the value of y {#sec:org562f238}

1.  This corresponds to the region below the curve $y=x^2$, with x from
    0 to 1. This can be seen as
    $\int_0^1 x^2 dx = \frac{x^3}{3} |_0^1 = \frac{1}{3}$. Given that
    the total area is 2, the probability of x^2^ being greater than or
    equal to y is $\frac{1}{6}$. [\[sec:org0a69f1d\]]{#sec:org0a69f1d
    label="sec:org0a69f1d"}

17. Countable additivity {#sec:org2e44841}
========================

Probability calculation: discrete but infinite sample space. {#sec:org6fc3cb2}
------------------------------------------------------------

### Sample space: $\{1,2,3,...\}$ {#sec:orgc3b5b85}

1.  For example, an experiment with a coin tossed and we are looking for
    the first time a heads occur. The first heads could be the first
    toss, second, third, etc so the sample space is discrete and
    infinite. [\[sec:org0b8efab\]]{#sec:org0b8efab
    label="sec:org0b8efab"}

2.  Let us specify a probability law.
    [\[sec:org16b170d\]]{#sec:org16b170d label="sec:org16b170d"}

    1.  We have $P(n) = \frac{1}{2^n}, n=1,2,3,...$
        [\[sec:org7cc5937\]]{#sec:org7cc5937 label="sec:org7cc5937"}

    2.  Do these add to 1? [\[sec:orgf6b9a05\]]{#sec:orgf6b9a05
        label="sec:orgf6b9a05"}

        1.  $\sum_{n=1}^{\infty} \frac{1}{2^n} = \frac{1}{2} \sum_{n=0}^{\infty} \frac{1}{2^n} = \frac{1}{2} * \frac{1}{1-(\frac{1}{2})}=1$
            [\[sec:org908b69f\]]{#sec:org908b69f label="sec:org908b69f"}

    3.  How can we calculate the probabilty of a general event?
        [\[sec:org9daea9a\]]{#sec:org9daea9a label="sec:org9daea9a"}

        1.  Probability that the outcome is even is equal to
            [\[sec:org4eadff5\]]{#sec:org4eadff5 label="sec:org4eadff5"}

        2.  $P(\{2,4,6,...\}) = P(\{2\} \cup \{4\} \cup \{6\} \cup ... ) = P(2)+P(4)+P(6)+... = \frac{1}{2^2} + \frac{1}{2^4} + \frac{1}{2^6} = \frac{1}{4}(1+\frac{1}{4} +\frac{1}{4^2}+...) = \frac{1}{4} \cdot \frac{1}{1-\frac{1}{4}} = \frac{1}{3}$
            [\[sec:org125d593\]]{#sec:org125d593 label="sec:org125d593"}

        3.  This leads to the Countable Additivity Axiom
            [\[sec:org610da07\]]{#sec:org610da07 label="sec:org610da07"}

            1.  If $A_1,A_2,...$ is an infinite sequence of disjoint
                events, then
                $P(A_1 \cup A_2 \cup ...) = P(A_1)+P(A_2)+...$
                [\[sec:org70a9e0e\]]{#sec:org70a9e0e
                label="sec:org70a9e0e"}

                1.  Having a sequence here is important.
                    [\[sec:org9e239ee\]]{#sec:org9e239ee
                    label="sec:org9e239ee"}

                    1.  Otherwise, we could say that a unit square with
                        a union of disjoint single elements, each with a
                        probability of 0, lead to $P(\Omega )=0$, which
                        cannot be the case.
                        [\[sec:org2b904d9\]]{#sec:org2b904d9
                        label="sec:org2b904d9"}

                    2.  Since the disjoint elements in the unit square
                        are not countable and cannot be arranged in a
                        sequence, the Countable Additivity Axiom does
                        not apply. [\[sec:org2cb7c43\]]{#sec:org2cb7c43
                        label="sec:org2cb7c43"}

18. Exercise: Using countable additivity {#sec:org75b1cc5}
========================================

Let the sample space be the set of positive integers and suppose that P(n)=1/2n, for n=1,2,.... Find the probability of the set {3,6,9,...}, that is, of the set of of positive integers that are multiples of 3. {#sec:org5437b55}
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### For this, we can use countable additivity {#sec:orgab452f0}

### $\frac{1}{2^3} + \frac{1}{2^6} + \frac{1}{2^9} +...= \frac{\frac{1}{2^3}}{1-(\frac{1}{2^3})} = 1/7$ {#sec:orgeaeedc4}

19. Exercise: Uniform probabilities on the integers {#sec:orgb3330a9}
===================================================

Let the sample space be the set of all positive integers. Is it possible to have a "uniform" probability law, that is, a probability law that assigns the same probability c to each positive integer? {#sec:orgffadb2e}
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### This cannot be the true. We have the following two cases: {#sec:org361519f}

1.  c=0 [\[sec:orgafe41a4\]]{#sec:orgafe41a4 label="sec:orgafe41a4"}

    1.  If c=0, then we have the following by countable additivity
        [\[sec:org6e49e73\]]{#sec:org6e49e73 label="sec:org6e49e73"}

        1.  $1=P(\Omega )=P(\{1\}\cup \{2\}\cup \{3\}\cup ...) = P(\{1\}) + P(\{2\}) +... = 0+0+...=0$
            [\[sec:orgb41d519\]]{#sec:orgb41d519 label="sec:orgb41d519"}

            1.  Thus we have $1=0$ which is a contradiction.
                [\[sec:org4ad4864\]]{#sec:org4ad4864
                label="sec:org4ad4864"}

2.  c\>0 [\[sec:orga4c9334\]]{#sec:orga4c9334 label="sec:orga4c9334"}

    1.  If c\>0, then there is some integer k such that kc\>1. k could
        simply be $\frac{1}{c}+1$. This would lead to the total
        probability being greater than 1, which cannot be the case.
        [\[sec:org2257812\]]{#sec:org2257812 label="sec:org2257812"}

20. Exercise: On countable additivity {#sec:org3e48232}
=====================================

Let the sample space be the two-dimensional plane. For any real number x, let Ax be the subset of the plane that consists of all points of the vertical line through the point $(x,0)$, i.e $A_x = \{\left( x,y \right): y \in Re\}$ {#sec:orgf764f83}
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### Do the axioms of probability theory imply that the probability of the union of the sets $A_x$ (which is the whole plane) is equal to the sum of the probabilities $P(A_x)$. {#sec:orgbee8c2b}

1.  No, they do not imply this. This is due to the fact that this
    collection of sets is not countable, as the set of real numbers is
    not countable. Thus the additivity axiom does not apply.
    [\[sec:org459cb74\]]{#sec:org459cb74 label="sec:org459cb74"}

### Do the axioms of probability theory imply that {#sec:org344be6f}

$P(A \cup A_2 \cup ...) = \sum_{x=1}^\infty P(A_x)$

1.  Yes, they do imply this. This is due to the fact that we are dealing
    with a sequence of disjoint events.
    [\[sec:org6f04c63\]]{#sec:org6f04c63 label="sec:org6f04c63"}

21. Interpretations and uses of probabilities {#sec:org9577916}
=============================================

Narrow view: {#sec:org4295648}
------------

### A branch of Mathematics {#sec:org327645d}

1.  Axioms $\implies$ theorems. [\[sec:org9286a8d\]]{#sec:org9286a8d
    label="sec:org9286a8d"}

2.  This can be looked at without looking at what probability really
    means [\[sec:org800e0a8\]]{#sec:org800e0a8 label="sec:org800e0a8"}

3.  "Theorem": Frequency of event A is $P(A)$
    [\[sec:org72e11d3\]]{#sec:org72e11d3 label="sec:org72e11d3"}

Are probabilities frequency? {#sec:orgff31172}
----------------------------

### P(Coin toss yields heads)=1/2 {#sec:org0cd8215}

1.  In this case, it makes sense to think of probability as a frequency
    [\[sec:org5240605\]]{#sec:org5240605 label="sec:org5240605"}

### P(The president of ... will be reelected)=0.7 {#sec:org30b9a34}

1.  Thinking of this as a frequency doesn't make as much sense, because
    there is only a single election.
    [\[sec:org96d060d\]]{#sec:org96d060d label="sec:org96d060d"}

Probabilities are often interpreted as: {#sec:orgd34deb5}
---------------------------------------

### Description of beliefs {#sec:orgfc3ef83}

### Betting preferences {#sec:orgac3f887}

The role of probability theory {#sec:orgfebff79}
------------------------------

### A framework for analyzing phenomena with uncertain outcomes {#sec:org4f9de17}

1.  Rules for consistent reasoning [\[sec:org207a71b\]]{#sec:org207a71b
    label="sec:org207a71b"}

2.  Used for predictions and decisions
    [\[sec:org489f500\]]{#sec:org489f500 label="sec:org489f500"}

Real world generates data which can be used by statistics to create models which can then be used by probability theory analysis that can be used to make real world predictions. {#sec:org8280931}
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
