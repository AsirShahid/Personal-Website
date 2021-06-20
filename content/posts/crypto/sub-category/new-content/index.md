---
title: "New Content"
date: 2020-06-08T08:06:25+06:00
description: Sample post with multiple images, embedded video ect.
menu:
  sidebar:
    name: Rich Content
    identifier: rich-content
    parent: sub-category
    weight: 10
hero: images/forest.jpg

---
# Table of Contents

1.  [1. Motivation](#org94d73fc)
    1.  [We need to be able to make decisions under uncertainty](#org2164f1b)
2.  [2. Lecture 1 overview and slides](#org2ff1620)
    1.  [Downloaded PDF for lecture slides](#orgcc746a9)
3.  [3. Sample space](#org77436a5)
    1.  [Two Steps:](#org5b1ef8c)
        1.  [Describe possible outcomes](#orgce41320)
        2.  [Describe beliefs about likelihood](#org0613713)
    2.  [List set of possible outcomes \(\Omega\)](#org2419954)
    3.  [The elements out our set should have some properties](#org8dd9b91)
        1.  [Mutually exclusive](#orgfade62a)
        2.  [Collectively exhaustive](#org0b46dcb)
        3.  [At the right granularity](#org58d5864)
    4.  [Ex.](#org4111814)
        1.  [Flipping a coin. Our outcomes are heads or tails.](#org6089cc5)
4.  [4. Exercise: Sample space](#org717f1ec)
    1.  [For the experiment of flipping a coin, and for each one of the following choices, determine whether we have a legitimate sample space:](#org7293125)
    2.  [$&Omega;$={Heads and it is raining, Heads and it is not raining, Tails}](#org7ffc2d1)
        1.  [Yes](#org7b3acce)
    3.  [$$P(A&cup; B&Omega;$={Heads and it is raining, Tails and it is not raining, Tails}](#orgd67bf40)
        1.  [No](#orgc14b969)
5.  [5. Sample space examples](#org41d69ac)
    1.  [Discrete/finite example](#org95b6623)
        1.  [Two rolls of a tetrahedral die](#org0092b48)
    2.  [Continuous example](#org8b21bd2)
        1.  [If we have a dart board, where we are throwing darts with X and Y axis, we can record the coordinates as real numbers with infinite precision. This gives us an infinite amount of possibilities for our sample space, thus we have a continuous sample space.](#org046a127)
6.  [6. Exercise: Tree representations](#orga2b6d40)
    1.  [Paul checks the weather forecast. If the forecast is good, Paul will go out for a walk. If the forecast is bad, then Paul will either stay home or go out. If he goes out, he might either remember or forget his umbrella. In the tree diagram below, identify the leaf that corresponds to the event that the forecast is bad and Paul stays home.](#orge8f0a3d)
        1.  [1 Represents the forecast being good, as the decision making ends there. Paul will definitely go for a walk.](#org586f26b)
        2.  [If the forecast is bad, we have choices to make. 2 represents the weather being good and Paul deciding to stay home.](#org8ddc992)
        3.  [If the forecast is bad, Paul could still go out. In which case he could either remember or forget his umbrella which would be 3 and 4.](#orgdc3d1c0)
7.  [7. Probability axioms](#org4fe6b11)
    1.  [Now we can see how to figure out which occurences are more/less likely to occur.](#orgaebcf33)
    2.  [However, we have an issue when it comes to continuous sample spaces.](#org54c4c46)
        1.  [The probability of hitting any single point on a continuous space is essentially 0.](#org18acbc7)
    3.  [Event: A subset of the sample space.](#orgd452dbe)
        1.  [We will instead assign probability to events.](#org7eb4855)
    4.  [Axioms:](#orgf8e2830)
        1.  [Nonnegativity: \(P(A)\ge 0\)](#org4e4c574)
        2.  [Normalization: \(P(\Omega)=1\)](#orge92b118)
        3.  [Finite Additivity:](#orgaf6e356)
        4.  [These axioms are the only ones that need to be stated. Anything else, such as \(P(A)\leq 1\) is already implied from our axioms.](#org7e1e9ff)
8.  [8. Exercise: Axioms](#org8d28cc8)
    1.  [Let A and B be events on the same sample space, with P(A)=0.6 and P(B)=0.7. Can these two events be disjoint?](#org895f00d)
        1.  [No because \(P(A)+P(B)>1\). If they were disjoint, then \(P(A)+P(B)=P(A\cup B)=1.3\) which is greater than 1. This would contradict the normalization axiom](#org3511d55)
9.  [9. Simple properties of probabilities](#orgfcf3937)
    1.  [Consequences of axioms:](#orge82bec5)
        1.  [(A) \(P(A)\ge 0\) implies that \(P(A)\le 1\)](#orgf04e270)
        2.  [(B) \(P(\Omega)=1\) implies that \(P(\varnothing)=0\)](#org7ae1f6c)
        3.  [(C) \(P(A\cup B)=P(A)+P(B)\) implies that \(P(A)+P(A^c)=1\) and that \(P(A\cup B\cup C)=P(A)+P(B)+P(C)\) for \(k\) disjoint sets.](#org8fdc6b0)
10. [10. Exercise: Simple properties](#org8676e75)
    1.  [Let A, B, and C be disjoint subsets of the sample space. For each one of the following statements, determine whether it is true or false. Note: &ldquo;False&rdquo; means &ldquo;not guaranteed to be true.](#org7f2ef64)
        1.  [\(P(A)+P(A^c)+P(B)=P(A\cup A^c\cup B)\)](#org4c18d44)
        2.  [\(P(A)+P(B)\le 1\)](#org63b267e)
        3.  [\(P(A^c)+P(B)\le 1\)](#org4c60d02)
        4.  [\(P(A\cup B\cup C)\ge P(A\cup B)\).](#org5d650ca)
11. [11. More properties of probabilities](#org4161d42)
    1.  [More consequences of axioms:](#org683feab)
        1.  [If \(A \subset B\), then \(P(A)\le P(B)\)](#orgde59740)
        2.  [\(P(A \cup B) = P(A) + P(B) -P(A \cap B)\) even if these sets are not disjoint.](#orgea3a767)
        3.  [\(P(A \cup B) \le P(A) + P(B)\)](#org899b4ab)
12. [12. Exercise: More properties](#org3ccefbf)
    1.  [Let A, B, and C be subsets of the sample space, not necessarily disjoint. For each one of the following statements, determine whether it is true or false. Note: “False&ldquo; means “not guaranteed to be true.&rdquo;](#org63029d1)
        1.  [\( P( (A \cap B) \cup (C \cap A^c) ) \le P(A \cup B \cup C) \)](#org3390bff)
        2.  [\( P( A \cup B \cup C ) = P( A \cap C^c ) + P(C) + P( B \cap A^c \cap C^c )\)](#orgaa5261c)
13. [13. A discrete example](#orgef3f556)
    1.  [We can move from the abstract to the concrete.](#orga5fe5be)
    2.  [When we have two rolls of a tetrahedral dice, we have 16 possible outcomes, all of which are equally likely.](#org6012a9d)
    3.  [\( P(X=1) = \frac{1}{4} \)](#org803185f)
        1.  [Where X is the value of the first roll.](#org4648541)
    4.  [Let \( Z=\min(X,Y) \)](#org66d96a5)
        1.  [\( P(Z=4)= \frac{1}{16}\)](#org7e253ce)
        2.  [\( P(Z=2) = \frac{1}{16} + \frac{2}{16} + \frac{2}{16} = \frac{5}{16} \)](#org529cc07)
    5.  [This example is something called a Discrete Uniform Law.](#orgf61849b)
        1.  [Assume \( \Omega  \) consists of \( n \) equally likely elements](#org1cbd839)
        2.  [Assume \( A \) consists of \( k \) elements](#org430ffd5)
        3.  [\( P(A) = k*\frac{1}{n} \)](#org6bf78bb)
14. [14. Exercise: Discrete probability calculations](#org8a22acd)
    1.  [Consider the same model of two rolls of a tetrahedral die, with all 16 outcomes equally likely. Find the probability of the following events:](#org80d1f7e)
        1.  [The value in the first roll is strictly larger than the value in the second roll.](#org6d917d3)
        2.  [The sum of the values obtained in the two rolls is an even number.](#org42168a0)
15. [15. A continuous example](#orga7f9e7c)
    1.  [Probability calculation: Continuous example](#org2e96979)
        1.  [\( \left( x,y \right) \) such that \( 0 \le x,y \le 1 \)](#org3ba0646)
    2.  [Probability calculation steps](#org155475c)
        1.  [Specify the sample space](#org9263ca2)
        2.  [Specify a probability law](#orgce3440a)
        3.  [Identify an event of interest](#org4f00ab8)
        4.  [Calculate](#orgb797c0b)
16. [16. Exercise: Continuous probability calculations](#org52905d6)
    1.  [Consider a sample space that is the rectangular region [0,1]×[0,2], i.e., the set of all pairs (x,y) that satisfy 0≤x≤1 and 0≤y≤2. Consider a “uniform&ldquo; probability law, under which the probability of an event is half of the area of the event. Find the probability of the following events:](#orgd8b507a)
        1.  [The two components x and y have the same values](#orgbf76033)
        2.  [The value, x, of the first component is larger than or equal to the value, y, of the second component.](#org774910a)
        3.  [The value of x<sup>2</sup> is larger than or equal to the value of y](#org3177608)
17. [17. Countable additivity](#org55ade95)
    1.  [Probability calculation: discrete but infinite sample space.](#org20778fc)
        1.  [Sample space: \( \{1,2,3,...\} \)](#org8f52c2e)
18. [18. Exercise: Using countable additivity](#org3f824bf)
    1.  [Let the sample space be the set of positive integers and suppose that P(n)=1/2n, for n=1,2,…. Find the probability of the set {3,6,9,…}, that is, of the set of of positive integers that are multiples of 3.](#orgb8275ae)
        1.  [For this, we can use countable additivity](#org7ba0263)
        2.  [\( \frac{1}{2^3} + \frac{1}{2^6} + \frac{1}{2^9} +...= \frac{\frac{1}{2^3}}{1-(\frac{1}{2^3})} = 1/7 \)](#org54e58e3)
19. [19. Exercise: Uniform probabilities on the integers](#orgf13b791)
    1.  [Let the sample space be the set of all positive integers. Is it possible to have a “uniform&ldquo; probability law, that is, a probability law that assigns the same probability c to each positive integer?](#orge8a847a)
        1.  [This cannot be the true. We have the following two cases:](#org8aebdac)
20. [20. Exercise: On countable additivity](#org995e4a8)
    1.  [Let the sample space be the two-dimensional plane. For any real number x, let Ax be the subset of the plane that consists of all points of the vertical line through the point \( (x,0) \), i.e \( A_x = \{\left( x,y \right): y \in Re\} \)](#org6a99008)
        1.  [Do the axioms of probability theory imply that the probability of the union of the sets \( A_x \) (which is the whole plane) is equal to the sum of the probabilities \( P(A_x) \).](#org254f0c2)
        2.  [Do the axioms of probability theory imply that](#orgcf4b3bc)
21. [21. Interpretations and uses of probabilities](#orga073868)
    1.  [Narrow view:](#orgcb4d89d)
        1.  [A branch of Mathematics](#org0580aa2)
    2.  [Are probabilities frequency?](#org12c12bd)
        1.  [P(Coin toss yields heads)=1/2](#org7d428d7)
        2.  [P(The president of &#x2026; will be reelected)=0.7](#orgad0e7f8)
    3.  [Probabilities are often interpreted as:](#org5efeb46)
        1.  [Description of beliefs](#org1e1fa7c)
        2.  [Betting preferences](#orgf1ad3ad)
    4.  [The role of probability theory](#orgbae60d1)
        1.  [A framework for analyzing phenomena with uncertain outcomes](#org7ec9610)
    5.  [Real world generates data which can be used by statistics to create models which can then be used by probability theory analysis that can be used to make real world predictions.](#orgb57f73a)



<a id="org94d73fc"></a>

# 1. Motivation


<a id="org2164f1b"></a>

## We need to be able to make decisions under uncertainty


<a id="org2ff1620"></a>

# 2. Lecture 1 overview and slides


<a id="orgcc746a9"></a>

## Downloaded PDF for lecture slides


<a id="org77436a5"></a>

# 3. Sample space


<a id="org5b1ef8c"></a>

## Two Steps:


<a id="orgce41320"></a>

### Describe possible outcomes


<a id="org0613713"></a>

### Describe beliefs about likelihood


<a id="org2419954"></a>

## List set of possible outcomes \(\Omega\)


<a id="org8dd9b91"></a>

## The elements out our set should have some properties


<a id="orgfade62a"></a>

### Mutually exclusive

1.  If one outcome happened, others can not happen


<a id="org0b46dcb"></a>

### Collectively exhaustive

1.  All the elements of the set make up all possibilities


<a id="org58d5864"></a>

### At the right granularity


<a id="org4111814"></a>

## Ex.


<a id="org6089cc5"></a>

### Flipping a coin. Our outcomes are heads or tails.

1.  Let&rsquo;s say we also looked outside while flipping the coin.

    1.  Either it&rsquo;s heads and rain, heads and no rain, tails and rain, or tails and no rain.
    
        1.  This is also a valid sample space.
        
        2.  However, since we are just curious about whether its heads or tails, this second sample space isn&rsquo;t as relevant.


<a id="org717f1ec"></a>

# 4. Exercise: Sample space


<a id="org7293125"></a>

## For the experiment of flipping a coin, and for each one of the following choices, determine whether we have a legitimate sample space:


<a id="org7ffc2d1"></a>

## $&Omega;$={Heads and it is raining, Heads and it is not raining, Tails}


<a id="org7b3acce"></a>

### Yes


<a id="orgd67bf40"></a>

## $$P(A&cup; B&Omega;$={Heads and it is raining, Tails and it is not raining, Tails}


<a id="orgc14b969"></a>

### No


<a id="org41d69ac"></a>

# 5. Sample space examples


<a id="org95b6623"></a>

## Discrete/finite example


<a id="org0092b48"></a>

### Two rolls of a tetrahedral die

1.  We have pairs of numbers. One containing the result of the first die and another containing the result of hte second die.

    1.  Result could be written as (1,1) if first die was 1 and second die was 1, (1,2) if first die was 1 and second die was 2, etc.

2.  Sequential description-

    1.  An experiment with several stages such as this can be described as a tree
    
        ![img](https://i.imgur.com/k6Hl4NP.png)
    
    2.  This shows us a distinction in the stages, with 16 different outcomes.


<a id="org8b21bd2"></a>

## Continuous example


<a id="org046a127"></a>

### If we have a dart board, where we are throwing darts with X and Y axis, we can record the coordinates as real numbers with infinite precision. This gives us an infinite amount of possibilities for our sample space, thus we have a continuous sample space.


<a id="orga2b6d40"></a>

# 6. Exercise: Tree representations


<a id="orge8f0a3d"></a>

## Paul checks the weather forecast. If the forecast is good, Paul will go out for a walk. If the forecast is bad, then Paul will either stay home or go out. If he goes out, he might either remember or forget his umbrella. In the tree diagram below, identify the leaf that corresponds to the event that the forecast is bad and Paul stays home.

![img](https://courses.edx.org/assets/courseware/v1/641ba94a18d06ac5698cf9a413c42bd2/asset-v1:MITx+6.431x+2T2021+type@asset+block/images_texshop_image.jpg)


<a id="org586f26b"></a>

### 1 Represents the forecast being good, as the decision making ends there. Paul will definitely go for a walk.


<a id="org8ddc992"></a>

### If the forecast is bad, we have choices to make. 2 represents the weather being good and Paul deciding to stay home.


<a id="orgdc3d1c0"></a>

### If the forecast is bad, Paul could still go out. In which case he could either remember or forget his umbrella which would be 3 and 4.


<a id="org4fe6b11"></a>

# 7. Probability axioms


<a id="orgaebcf33"></a>

## Now we can see how to figure out which occurences are more/less likely to occur.


<a id="org54c4c46"></a>

## However, we have an issue when it comes to continuous sample spaces.


<a id="org18acbc7"></a>

### The probability of hitting any single point on a continuous space is essentially 0.


<a id="orgd452dbe"></a>

## Event: A subset of the sample space.


<a id="org7eb4855"></a>

### We will instead assign probability to events.

1.  \(P(A)\)

2.  So even though individual events have 0 probablity, these events have some probability.


<a id="orgf8e2830"></a>

## Axioms:


<a id="org4e4c574"></a>

### Nonnegativity: \(P(A)\ge 0\)


<a id="orge92b118"></a>

### Normalization: \(P(\Omega)=1\)

1.  The probability of our sample space occuring is 1.


<a id="orgaf6e356"></a>

### Finite Additivity:

If \(A \cap B = \varnothing\), then \(P(A \cup B)=P(A)+P(B)\)

1.  When the intersection between A and B is the empty set, then they are considered disjoint. Then \(P(A\cup B)=P(A)+P(B)\)

    1.  This is due to the fact that there is no overlap in \(P(A)\) or \(P(B)\).

2.  This axiom needs to be refined and strengthened later.


<a id="org7e1e9ff"></a>

### These axioms are the only ones that need to be stated. Anything else, such as \(P(A)\leq 1\) is already implied from our axioms.


<a id="org8d28cc8"></a>

# 8. Exercise: Axioms


<a id="org895f00d"></a>

## Let A and B be events on the same sample space, with P(A)=0.6 and P(B)=0.7. Can these two events be disjoint?


<a id="org3511d55"></a>

### No because \(P(A)+P(B)>1\). If they were disjoint, then \(P(A)+P(B)=P(A\cup B)=1.3\) which is greater than 1. This would contradict the normalization axiom


<a id="orgfcf3937"></a>

# 9. Simple properties of probabilities


<a id="orge82bec5"></a>

## Consequences of axioms:


<a id="orgf04e270"></a>

### (A) \(P(A)\ge 0\) implies that \(P(A)\le 1\)


<a id="org7ae1f6c"></a>

### (B) \(P(\Omega)=1\) implies that \(P(\varnothing)=0\)


<a id="org8fdc6b0"></a>

### (C) \(P(A\cup B)=P(A)+P(B)\) implies that \(P(A)+P(A^c)=1\) and that \(P(A\cup B\cup C)=P(A)+P(B)+P(C)\) for \(k\) disjoint sets.

1.  An element and its compliment makes up \(\Omega\) and the intersection of a set and its compliment is \(\varnothing\).

2.  From (B), \(P(\Omega)=1\) which is equal to \(P(A\cup A^c)\). This is equal to \(P(A)+P(A^c)\).

    1.  Based on this, we can write that \(P(A)=1-P(A^c)\le 1\).

3.  \(1=P(\Omega)+P(\Omega^c)\)

    1.  \(1=1+P(\Omega^c) \Rightarrow 1=1+P(\varnothing)\Rightarrow P(\varnothing)=0\)

4.  When \(A,B,C\) are disjoint, \(P(A\cup B\cup C)=P(A)+P(B)+P(C)\).

    1.  We can think of the \(P(A\cup B\cup C)\) as \(P((A\cup B)\cup C)=P(A\cup B)+P(C)=P(A)+P(B)+P(C)\)
    
        1.  This logic can be continued for \(k\) disjoint sets. Can prove by induction.
        
        2.  If \((A_1,\cdots ,A_k)\) then \(P(A_1\cup \cdots \cup A_k = \sum_{i=1}^{k}P(A_i)\)

5.  \(P(\{s_1,s_2,\cdots,s_k\}) = P(\{s_1\}\cup\cdots \cup \{s_k\}) = P(\{s_1\})+\cdots + P(\{s_k\})=P(s_1)+\cdots + P(s_k)\)


<a id="org8676e75"></a>

# 10. Exercise: Simple properties


<a id="org7f2ef64"></a>

## Let A, B, and C be disjoint subsets of the sample space. For each one of the following statements, determine whether it is true or false. Note: &ldquo;False&rdquo; means &ldquo;not guaranteed to be true.


<a id="org4c18d44"></a>

### \(P(A)+P(A^c)+P(B)=P(A\cup A^c\cup B)\)

1.  This statement is false. While A and the compliment of A are known to be disjoint, we do not know if this also applies to A and B or \(A^c\) and B.


<a id="org63b267e"></a>

### \(P(A)+P(B)\le 1\)

1.  This statement is true since A and B are disjoint, \(P(A)+P(B)=P(A\cup B)\) which can not be greater than 1.


<a id="org4c60d02"></a>

### \(P(A^c)+P(B)\le 1\)

1.  This is false. For example, consider A situation where \(A=\varnothing\). Then \(A^c=\Omega\). Now given that A and B are disjoint, no matter what B is, \(P(\Omega)+P(B)>1\).


<a id="org5d650ca"></a>

### \(P(A\cup B\cup C)\ge P(A\cup B)\).

1.  This must be true. Given that these are disjoint, we know that \(P(A\cup B\cup C)=P(A)+P(B)+P(C)\). And we also know that \(P(A\cup B)= P(A)+P(B)\). So given that the probability of an event must be nonnegative, we know \(P(A\cup B\cup C)\) must be greater than or equal to \(P(A\cup B)\).


<a id="org4161d42"></a>

# 11. More properties of probabilities


<a id="org683feab"></a>

## More consequences of axioms:


<a id="orgde59740"></a>

### If \(A \subset B\), then \(P(A)\le P(B)\)

1.  This seems obvious, but how can we prove this?

    1.  \(B\) can be written as \(A \cup (B \cap A^c)\).
    
    2.  Thus \(P(B)=P(A) +P(B \cap A^c)\ge P(A)\)
    
    3.  So since probabilities are nonnegative, we know that \( P(A) \le P(B) \)


<a id="orgea3a767"></a>

### \(P(A \cup B) = P(A) + P(B) -P(A \cap B)\) even if these sets are not disjoint.

1.  The union of A and B can be broken down into 3 distinct parts.

    1.  \(a=P(A \cap B^c)\)
    
    2.  \(b=P(A \cap B)\)
    
    3.  \(c=P(B  \cap A^c)\)

2.  Then \(P(A \cup B) =a+b+c\)

    1.  \(P(A)+P(B)-P(A\cap B)=(a+b)+(b+c)-b=a+b+c\)
    
    2.  Thus we can see that this is true.

3.  This leads us to the following union bound:


<a id="org899b4ab"></a>

### \(P(A \cup B) \le P(A) + P(B)\)

1.  This is called the union bound and can be used when proving the probability of something is less than the probability of something else.

2.  \( P(A \cup B \cup C) = P(A) +P(A^c \cap B) + P(A^c \cap B^c \cap C) \)

    1.  We have several pieces:
    
        1.  \( A \cup B \cup C=A \cup (B \cap A^c) \cup (C \cap A^c \cap B^c) \)
    
    2.  These three pieces are disjoint, thus the additivity axiom gives us:
    
        1.  \( P(A \cup B \cup C)=P(A)+ P(\cup (B \cap A^c)) + P(C \cap A^c \cap B^c) \)


<a id="org3ccefbf"></a>

# 12. Exercise: More properties


<a id="org63029d1"></a>

## Let A, B, and C be subsets of the sample space, not necessarily disjoint. For each one of the following statements, determine whether it is true or false. Note: “False&ldquo; means “not guaranteed to be true.&rdquo;


<a id="org3390bff"></a>

### \( P( (A \cap B) \cup (C \cap A^c) ) \le P(A \cup B \cup C) \)

1.  This statement must be true. This is due to the fact that \( A \cap B \) cannot be any bigger than \( A \cup B \) and \( C \cap A^c \) cannot be any bigger than \( C \). Thus this statement is true.


<a id="orgaa5261c"></a>

### \( P( A \cup B \cup C ) = P( A \cap C^c ) + P(C) + P( B \cap A^c \cap C^c )\)

1.  This statement must be true. It is the same property we saw earlier in 11.


<a id="orgef3f556"></a>

# 13. A discrete example


<a id="orga5fe5be"></a>

## We can move from the abstract to the concrete.


<a id="org6012a9d"></a>

## When we have two rolls of a tetrahedral dice, we have 16 possible outcomes, all of which are equally likely.


<a id="org803185f"></a>

## \( P(X=1) = \frac{1}{4} \)


<a id="org4648541"></a>

### Where X is the value of the first roll.


<a id="org66d96a5"></a>

## Let \( Z=\min(X,Y) \)


<a id="org7e253ce"></a>

### \( P(Z=4)= \frac{1}{16}\)


<a id="org529cc07"></a>

### \( P(Z=2) = \frac{1}{16} + \frac{2}{16} + \frac{2}{16} = \frac{5}{16} \)


<a id="orgf61849b"></a>

## This example is something called a Discrete Uniform Law.


<a id="org1cbd839"></a>

### Assume \( \Omega  \) consists of \( n \) equally likely elements


<a id="org430ffd5"></a>

### Assume \( A \) consists of \( k \) elements


<a id="org6bf78bb"></a>

### \( P(A) = k*\frac{1}{n} \)


<a id="org8a22acd"></a>

# 14. Exercise: Discrete probability calculations


<a id="org80d1f7e"></a>

## Consider the same model of two rolls of a tetrahedral die, with all 16 outcomes equally likely. Find the probability of the following events:


<a id="org6d917d3"></a>

### The value in the first roll is strictly larger than the value in the second roll.

1.  This event contains the times the first roll is strictly larger than the second. The first will be equal to the second a fourth of the time. The two rolls are not equal \( \frac{3}{4} \) of the time, which in this case means 12 of the 16 rolls will not be equal. In half of these occurences, the first roll will be greater than the second roll, and vice versa in the other half. Thus, we have a \( \frac{6}{16} \) probability that the first roll will be strictly greater than the second.


<a id="org42168a0"></a>

### The sum of the values obtained in the two rolls is an even number.

1.  This event will happen half the time, since half our numbers are even numbers and half are odd. So the probability will be \( \frac{8}{16} \)


<a id="orga7f9e7c"></a>

# 15. A continuous example


<a id="org2e96979"></a>

## Probability calculation: Continuous example


<a id="org3ba0646"></a>

### \( \left( x,y \right) \) such that \( 0 \le x,y \le 1 \)

1.  We need to specify a uniform probability law

    1.  Meaning, the probability is equal to the area.
    
    2.  \( P( \{\left( x,y \right) | x+y \le \frac{1}{2} \} ) \)
    
        1.  These points form a triangle between the line \( x+y=\frac{1}{2} \)
        
        2.  So the probability is equal to the area of the triangle which is \( \frac{1}{2} * \frac{1}{2} * \frac{1}{2} = \frac{1}{8} \)
    
    3.  \( P(\{\left( 0.5,0.3 \right)\}) \)
    
        1.  This event consists of only one element, a single point.
        
        2.  The area of a single point is 0, so the probability of having this single point, or any other single point, is simply 0.


<a id="org155475c"></a>

## Probability calculation steps


<a id="org9263ca2"></a>

### Specify the sample space


<a id="orgce3440a"></a>

### Specify a probability law


<a id="org4f00ab8"></a>

### Identify an event of interest


<a id="orgb797c0b"></a>

### Calculate


<a id="org52905d6"></a>

# 16. Exercise: Continuous probability calculations


<a id="orgd8b507a"></a>

## Consider a sample space that is the rectangular region [0,1]×[0,2], i.e., the set of all pairs (x,y) that satisfy 0≤x≤1 and 0≤y≤2. Consider a “uniform&ldquo; probability law, under which the probability of an event is half of the area of the event. Find the probability of the following events:


<a id="orgbf76033"></a>

### The two components x and y have the same values

1.  This event is simply a line, which has no area. Thus the probability of this will be \( 0 \).


<a id="org774910a"></a>

### The value, x, of the first component is larger than or equal to the value, y, of the second component.

1.  This would make up a triangle with points at \( (0,1),(1,0),(1,1) \). The area of such a triangle is 0.5 and the total area of the region is 2. Thus the probability of the x value being larger than the y value is \( \frac{1}{4} \)


<a id="org3177608"></a>

### The value of x<sup>2</sup> is larger than or equal to the value of y

1.  This corresponds to the region below the curve \( y=x^2 \), with x from 0 to 1. This can be seen as \( \int_0^1 x^2 dx = \frac{x^3}{3} |_0^1 = \frac{1}{3} \). Given that the total area is 2, the probability of x<sup>2</sup> being greater than or equal to y is \( \frac{1}{6} \).


<a id="org55ade95"></a>

# 17. Countable additivity


<a id="org20778fc"></a>

## Probability calculation: discrete but infinite sample space.


<a id="org8f52c2e"></a>

### Sample space: \( \{1,2,3,...\} \)

1.  For example, an experiment with a coin tossed and we are looking for the first time a heads occur. The first heads could be the first toss, second, third, etc so the sample space is discrete and infinite.

2.  Let us specify a probability law.

    1.  We have \( P(n) = \frac{1}{2^n}, n=1,2,3,... \)
    
    2.  Do these add to 1?
    
        1.  \( \sum_{n=1}^{\infty} \frac{1}{2^n} = \frac{1}{2} \sum_{n=0}^{\infty} \frac{1}{2^n} = \frac{1}{2} * \frac{1}{1-(\frac{1}{2})}=1 \)
    
    3.  How can we calculate the probabilty of a general event?
    
        1.  Probability that the outcome is even is equal to
        
        2.  \( P(\{2,4,6,...\}) = P(\{2\} \cup \{4\} \cup \{6\} \cup ... ) = P(2)+P(4)+P(6)+... = \frac{1}{2^2} + \frac{1}{2^4} + \frac{1}{2^6} = \frac{1}{4}(1+\frac{1}{4} +\frac{1}{4^2}+...) = \frac{1}{4} \cdot \frac{1}{1-\frac{1}{4}} = \frac{1}{3} \)
        
        3.  This leads to the Countable Additivity Axiom
        
            1.  If \( A_1,A_2,... \) is an infinite sequence of disjoint events, then \( P(A_1 \cup A_2 \cup ...) = P(A_1)+P(A_2)+... \)
            
                1.  Having a sequence here is important.
                
                    1.  Otherwise, we could say that a unit square with a union of disjoint single elements, each with a probability of 0, lead to \( P(\Omega )=0 \), which cannot be the case.
                    
                    2.  Since the disjoint elements in the unit square are not countable and cannot be arranged in a sequence, the Countable Additivity Axiom does not apply.


<a id="org3f824bf"></a>

# 18. Exercise: Using countable additivity


<a id="orgb8275ae"></a>

## Let the sample space be the set of positive integers and suppose that P(n)=1/2n, for n=1,2,…. Find the probability of the set {3,6,9,…}, that is, of the set of of positive integers that are multiples of 3.


<a id="org7ba0263"></a>

### For this, we can use countable additivity


<a id="org54e58e3"></a>

### \( \frac{1}{2^3} + \frac{1}{2^6} + \frac{1}{2^9} +...= \frac{\frac{1}{2^3}}{1-(\frac{1}{2^3})} = 1/7 \)


<a id="orgf13b791"></a>

# 19. Exercise: Uniform probabilities on the integers


<a id="orge8a847a"></a>

## Let the sample space be the set of all positive integers. Is it possible to have a “uniform&ldquo; probability law, that is, a probability law that assigns the same probability c to each positive integer?


<a id="org8aebdac"></a>

### This cannot be the true. We have the following two cases:

1.  c=0

    1.  If c=0, then we have the following by countable additivity
    
        1.  \( 1=P(\Omega )=P(\{1\}\cup \{2\}\cup \{3\}\cup ...) = P(\{1\}) + P(\{2\}) +... = 0+0+...=0\)
        
            1.  Thus we have \( 1=0 \) which is a contradiction.

2.  c>0

    1.  If c>0, then there is some integer k such that kc>1. k could simply be \( \frac{1}{c}+1 \). This would lead to the total probability being greater than 1, which cannot be the case.


<a id="org995e4a8"></a>

# 20. Exercise: On countable additivity


<a id="org6a99008"></a>

## Let the sample space be the two-dimensional plane. For any real number x, let Ax be the subset of the plane that consists of all points of the vertical line through the point \( (x,0) \), i.e \( A_x = \{\left( x,y \right): y \in Re\} \)


<a id="org254f0c2"></a>

### Do the axioms of probability theory imply that the probability of the union of the sets \( A_x \) (which is the whole plane) is equal to the sum of the probabilities \( P(A_x) \).

1.  No, they do not imply this. This is due to the fact that this collection of sets is not countable, as the set of real numbers is not countable. Thus the additivity axiom does not apply.


<a id="orgcf4b3bc"></a>

### Do the axioms of probability theory imply that

\( P(A \cup A_2 \cup ...) = \sum_{x=1}^\infty P(A_x)   \)

1.  Yes, they do imply this. This is due to the fact that we are dealing with a sequence of disjoint events.


<a id="orga073868"></a>

# 21. Interpretations and uses of probabilities


<a id="orgcb4d89d"></a>

## Narrow view:


<a id="org0580aa2"></a>

### A branch of Mathematics

1.  Axioms \( \implies \) theorems.

2.  This can be looked at without looking at what probability really means

3.  &ldquo;Theorem&rdquo;: Frequency of event A is \( P(A) \)


<a id="org12c12bd"></a>

## Are probabilities frequency?


<a id="org7d428d7"></a>

### P(Coin toss yields heads)=1/2

1.  In this case, it makes sense to think of probability as a frequency


<a id="orgad0e7f8"></a>

### P(The president of &#x2026; will be reelected)=0.7

1.  Thinking of this as a frequency doesn&rsquo;t make as much sense, because there is only a single election.


<a id="org5efeb46"></a>

## Probabilities are often interpreted as:


<a id="org1e1fa7c"></a>

### Description of beliefs


<a id="orgf1ad3ad"></a>

### Betting preferences


<a id="orgbae60d1"></a>

## The role of probability theory


<a id="org7ec9610"></a>

### A framework for analyzing phenomena with uncertain outcomes

1.  Rules for consistent reasoning

2.  Used for predictions and decisions


<a id="orgb57f73a"></a>

## Real world generates data which can be used by statistics to create models which can then be used by probability theory analysis that can be used to make real world predictions.

