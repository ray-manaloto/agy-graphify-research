---
doc_id: okf-colibri-v1-5-model-grading-report
title: Colibri v1.5.0 Multi-Model Evaluation & Grading Report
description: Comparative evaluation across all supported Colibri v1.5.0 inference models using the 100-Point Grading Matrix.
type: report
version: 1.5.0
spec_version: 1.0.0
---

# Colibri v1.5.0 Multi-Model Evaluation & Grading Report

Comparative evaluation across all supported Colibri v1.5.0 inference models using the 100-Point Grading Matrix.

## Overview

| Rank | Model Name | Parameter Scale | Nodes | Edges | Latency (s) | Total Score / 100 |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **#1** | `glm-5.2` | 744B | 110 | 90 | 0.043s | **75.68 / 100** |
| **#2** | `inkling` | 975B | 110 | 90 | 0.029s | **75.68 / 100** |
| **#3** | `kimi-k3` | 2.8T | 110 | 90 | 0.031s | **75.68 / 100** |
| **#4** | `deepseek-v4-flash` | 284B | 110 | 90 | 0.032s | **75.68 / 100** |
| **#5** | `olmoe-7b` | 7B | 110 | 90 | 0.027s | **75.68 / 100** |

## Detailed Category Breakdown

| Model Name | Entity Precision (25) | Relationship Richness (25) | Topology (20) | Performance (15) | Compliance (15) | Total (100) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `glm-5.2` | 25.0 | 16.55 | 4.13 | 15.0 | 15.0 | **75.68** |
| `inkling` | 25.0 | 16.55 | 4.13 | 15.0 | 15.0 | **75.68** |
| `kimi-k3` | 25.0 | 16.55 | 4.13 | 15.0 | 15.0 | **75.68** |
| `deepseek-v4-flash` | 25.0 | 16.55 | 4.13 | 15.0 | 15.0 | **75.68** |
| `olmoe-7b` | 25.0 | 16.55 | 4.13 | 15.0 | 15.0 | **75.68** |