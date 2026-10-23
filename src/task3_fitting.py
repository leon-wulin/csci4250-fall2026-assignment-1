"""Descriptive MLE candidates; no iid p-values or universal power-law claims."""
from __future__ import annotations

import math
import numpy as np
from scipy import optimize, special, stats


def candidate_cdf(candidate: dict, values: np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    p, method = candidate["parameters"], candidate["method"]
    if method == "binomial_reference":
        return stats.binom.cdf(x, p["trials"], p["p"])
    if method in ("hurdle_shifted_poisson", "hurdle_shifted_nbinom"):
        inner = (stats.poisson.cdf(x - 1, p["mu"]) if method.endswith("poisson")
                 else stats.nbinom.cdf(x - 1, p["r"], p["p"]))
        return np.where(x < 0, 0, np.where(x < 1, p["p0"], p["p0"] + (1 - p["p0"]) * inner))
    if method in ("bounded_binomial", "bounded_beta_binomial"):
        y = x - p["lower"]
        return (stats.binom.cdf(y, p["trials"], p["p"]) if method == "bounded_binomial"
                else stats.betabinom.cdf(y, p["trials"], p["a"], p["b"]))
    if method == "bounded_discrete_normal":
        low = stats.norm.cdf((p["lower"] - 0.5 - p["mu"]) / p["sigma"])
        high = stats.norm.cdf((p["upper"] + 0.5 - p["mu"]) / p["sigma"])
        cdf = (stats.norm.cdf((x + 0.5 - p["mu"]) / p["sigma"]) - low) / max(high - low, 1e-300)
        return np.where(x < p["lower"], 0, np.where(x >= p["upper"], 1, np.clip(cdf, 0, 1)))
    if method == "discrete_power_law_tail":
        cdf = 1 - special.zeta(p["alpha"], np.maximum(x + 1, 1)) / special.zeta(p["alpha"], p["xmin"])
        return np.where(x < p["xmin"], 0, np.clip(cdf, 0, 1))
    if method == "discretized_lognormal_tail":
        denominator = stats.norm.sf((np.log(p["xmin"] - 0.5) - p["mu"]) / p["sigma"])
        survival = stats.norm.sf((np.log(np.maximum(x + 0.5, 1e-300)) - p["mu"]) / p["sigma"])
        return np.where(x < p["xmin"], 0, np.clip(1 - survival / max(denominator, 1e-300), 0, 1))
    raise ValueError(f"Unknown discrete method: {method}")


def candidate_pmf(candidate: dict, values: np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    return np.maximum(0, candidate_cdf(candidate, x) - candidate_cdf(candidate, x - 1))


def ks_distance(samples: np.ndarray, cdf, *, discrete: bool = True) -> float:
    """Compare both sides of empirical jumps; account for integer gaps correctly."""
    x, counts = np.unique(samples, return_counts=True)
    right = np.cumsum(counts) / len(samples)
    left = right - counts / len(samples)
    model_right = cdf(x)
    model_left = cdf(x - 1) if discrete else model_right
    return float(max(np.max(np.abs(right - model_right)), np.max(np.abs(left - model_left))))


def scored(samples: np.ndarray, method: str, parameters: dict, k: int) -> dict:
    candidate = {"method": method, "parameters": parameters, "n_fit": len(samples), "parameter_count": k}
    probabilities = candidate_pmf(candidate, np.asarray(samples))
    log_likelihood = float(np.log(np.maximum(probabilities, 1e-300)).sum())
    candidate.update(log_likelihood=log_likelihood, aic=2 * k - 2 * log_likelihood,
                     ks=ks_distance(samples, lambda x: candidate_cdf(candidate, x)))
    return candidate


def unavailable(reason: str, scope: str, candidates: list | None = None) -> dict:
    return {"status": "N/A", "method": "N/A", "reason": reason, "fit_scope": scope,
            "parameters": {}, "n_fit": 0, "scope_weight": 0.0, "candidates": candidates or []}


def choose(candidates: list[dict], config: dict, scope: str, weight: float = 1.0) -> dict:
    eligible = [c for c in candidates if c["ks"] <= config["descriptive_ks_screen"] and not c.get("boundary_warning", False)]
    if not eligible:
        best = min(candidates, key=lambda c: c["ks"])
        return unavailable(f"Candidate mismatch: best KS={best['ks']:.3f} exceeds the descriptive screen, or optimization is boundary-limited.", scope, candidates)
    selected = min(eligible, key=lambda c: c["aic"])
    return {**selected, "status": "descriptive_fit", "reason": "Lowest AIC among screened candidates; descriptive only, not a significance test.",
            "fit_scope": scope, "scope_weight": float(weight), "candidates": candidates}


def hurdle_counts(samples: np.ndarray, config: dict, *, scope: str, weight: float = 1.0) -> dict:
    """Fit positive integer body as 1+Poisson or 1+NB; preserve any zero atom."""
    x = np.asarray(samples, dtype=int)
    if len(x) < config["minimum_fit_samples"] or len(np.unique(x)) < 3:
        return unavailable(f"Only {len(x)} observations or fewer than three distinct values; no stable parametric fit.", scope)
    positive = x[x > 0] - 1
    if len(positive) < config["minimum_fit_samples"] or positive.mean() == 0:
        return unavailable("Too few nondegenerate positive observations for a count model.", scope)
    p0 = float(np.mean(x == 0))
    mu = float(positive.mean())
    atom_k = int(0 < p0 < 1)
    poisson = scored(x, "hurdle_shifted_poisson", {"p0": p0, "mu": mu}, 1 + atom_k)

    def loss(log_r):
        r = math.exp(float(log_r))
        return -float(stats.nbinom.logpmf(positive, r, r / (r + mu)).sum())

    fit = optimize.minimize_scalar(loss, bounds=(-8, 15), method="bounded")
    candidates = [poisson]
    if fit.success and np.isfinite(fit.fun):
        r = math.exp(float(fit.x))
        candidates.append(scored(x, "hurdle_shifted_nbinom", {"p0": p0, "mu": mu, "r": r, "p": r / (r + mu)}, 2 + atom_k))
    return choose(candidates, config, scope, weight)


def eccentricity_fit(samples: np.ndarray, config: dict) -> dict:
    x = np.asarray(samples, dtype=int)
    lower, upper = int(x.min()), int(x.max())
    if len(x) < config["minimum_fit_samples"] or len(np.unique(x)) < 3:
        return unavailable("Degenerate or too few observations/distinct eccentricities for a shape fit.", "LCC nodes")
    trials = upper - lower
    probability = float((x.mean() - lower) / trials)
    candidates = [scored(x, "bounded_binomial", {"lower": lower, "trials": trials, "p": probability}, 1)]
    y = x - lower

    def beta_loss(log_ab):
        a, b = np.exp(log_ab)
        return -float(stats.betabinom.logpmf(y, trials, a, b).sum())

    fit = optimize.minimize(beta_loss, np.log([max(probability * 10, 0.1), max((1 - probability) * 10, 0.1)]),
                            bounds=[(-8, 12), (-8, 12)], method="L-BFGS-B")
    if fit.success and np.isfinite(fit.fun):
        a, b = map(float, np.exp(fit.x))
        candidates.append(scored(x, "bounded_beta_binomial", {"lower": lower, "trials": trials, "a": a, "b": b}, 2))

    def normal_loss(theta):
        candidate = {"method": "bounded_discrete_normal", "parameters": {"lower": lower, "upper": upper, "mu": float(theta[0]), "sigma": math.exp(float(theta[1]))}}
        return -float(np.log(np.maximum(candidate_pmf(candidate, x), 1e-300)).sum())

    fit = optimize.minimize(normal_loss, [x.mean(), math.log(max(float(x.std()), 0.2))],
                            bounds=[(lower - 3 * trials, upper + 3 * trials), (-4, math.log(10 * trials))], method="L-BFGS-B")
    if fit.success and np.isfinite(fit.fun):
        candidates.append(scored(x, "bounded_discrete_normal", {"lower": lower, "upper": upper, "mu": float(fit.x[0]), "sigma": math.exp(float(fit.x[1]))}, 2))
    return choose(candidates, config, "LCC nodes; support fixed to observed radius..diameter")


def power_tail_fit(samples: np.ndarray, config: dict) -> dict:
    """Exact discrete zeta MLE + KS xmin; compare lognormal on identical tail data."""
    values = np.asarray(samples, dtype=int)
    minimum = max(config["minimum_tail_samples"], math.ceil(0.02 * len(values)))
    fits = []
    for xmin in np.unique(values[values >= 1]):
        tail = values[values >= xmin]
        if len(tail) < minimum or len(np.unique(tail)) < config["minimum_tail_distinct_values"]:
            continue
        log_sum = float(np.log(tail).sum())
        objective = lambda alpha: alpha * log_sum + len(tail) * math.log(float(special.zeta(alpha, int(xmin))))
        result = optimize.minimize_scalar(objective, bounds=(1.01, 8), method="bounded")
        if result.success:
            fits.append(scored(tail, "discrete_power_law_tail", {"xmin": int(xmin), "alpha": float(result.x)}, 1))
    if not fits:
        return unavailable(f"No tail with at least {minimum} observations and sufficient distinct integer degrees.", "positive degree tail")
    power = min(fits, key=lambda c: (c["ks"], -c["n_fit"], c["parameters"]["xmin"]))
    xmin = power["parameters"]["xmin"]
    tail = values[values >= xmin]

    def lognormal_loss(theta):
        mu, sigma = float(theta[0]), math.exp(float(theta[1]))
        denominator = stats.norm.sf((math.log(xmin - 0.5) - mu) / sigma)
        left = stats.norm.sf((np.log(tail - 0.5) - mu) / sigma)
        right = stats.norm.sf((np.log(tail + 0.5) - mu) / sigma)
        return -float(np.log(np.maximum((left - right) / max(denominator, 1e-300), 1e-300)).sum())

    fit = optimize.minimize(lognormal_loss, [np.log(tail).mean(), math.log(max(float(np.log(tail).std()), 0.2))],
                            bounds=[(-20, 20), (-4, 3)], method="L-BFGS-B")
    candidates = [power]
    if fit.success and np.isfinite(fit.fun):
        candidate = scored(tail, "discretized_lognormal_tail", {"xmin": xmin, "mu": float(fit.x[0]), "sigma": math.exp(float(fit.x[1]))}, 2)
        candidate["boundary_warning"] = bool(abs(float(fit.x[0])) > 19.99 or abs(float(fit.x[1]) - 3) < 0.01 or abs(float(fit.x[1]) + 4) < 0.01)
        candidates.append(candidate)
    result = choose(candidates, config, f"degree >= {xmin}; body shown empirically, not fitted", len(tail) / len(values))
    result["xmin_search"] = {"method": "minimum discrete KS among zeta MLE candidates", "minimum_tail_samples": minimum,
                              "evaluated_thresholds": len(fits), "selected_xmin": xmin}
    return result


def reflected_probability(left, right, centers, weights, bandwidth):
    """Integrate three reflected Gaussian kernels and normalize exactly on [0,1]."""
    centers = np.asarray(centers)
    weights = np.asarray(weights, dtype=float)
    weights /= weights.sum()

    def integral(a, b):
        result = np.zeros(len(np.atleast_1d(a)))
        a, b = np.atleast_1d(a)[:, None], np.atleast_1d(b)[:, None]
        for mirrored in (centers, -centers, 2 - centers):
            mass = stats.norm.cdf((b - mirrored) / bandwidth) - stats.norm.cdf((a - mirrored) / bandwidth)
            result += mass @ weights
        return result

    return integral(left, right) / integral([0.0], [1.0])[0]


def clustering_fit(samples: np.ndarray, config: dict) -> dict:
    x = np.asarray(samples, dtype=float)
    interior = x[(x > 0) & (x < 1)]
    p0, p1 = float(np.mean(x == 0)), float(np.mean(x == 1))
    if len(interior) < config["minimum_fit_samples"] or len(np.unique(interior)) < 3:
        result = unavailable(f"Only {len(interior)} interior observations; endpoint atoms retained, no stable continuous fit.", "interior 0<C<1; separate exact endpoint masses")
        result["endpoint_masses"] = {"p0": p0, "p1": p1}
        return result
    try:
        a, b, _, _ = stats.beta.fit(interior, floc=0, fscale=1)
    except (ValueError, RuntimeError) as error:
        return unavailable(f"Beta interior optimization failed: {type(error).__name__}", "interior 0<C<1")
    ll = float(stats.beta.logpdf(interior, a, b).sum())
    ks = ks_distance(interior, lambda t: stats.beta.cdf(t, a, b), discrete=False)
    candidate = {"method": "zero_one_inflated_beta", "parameters": {"a": float(a), "b": float(b), "p0": p0, "p1": p1},
                 "n_fit": len(interior), "parameter_count": 2, "log_likelihood": ll, "aic": 4 - 2 * ll, "ks": ks}
    result = choose([candidate], config, "interior 0<C<1; empirical point masses at 0 and 1")
    result["endpoint_masses"] = {"p0": p0, "p1": p1}
    if result["status"] == "N/A":
        bandwidth = float(interior.std(ddof=1) * len(interior) ** (-0.2))
        centers, weights = np.unique(interior, return_counts=True)
        cdf = lambda t: reflected_probability(np.zeros_like(t), t, centers, weights, bandwidth)
        smoother = {"method": "reflected_kde_mixture", "parameters": {"bandwidth": bandwidth, "p0": p0, "p1": p1,
                    "bandwidth_rule": "sample standard deviation times n_interior^(-1/5)"},
                    "n_fit": len(interior), "ks": ks_distance(interior, cdf, discrete=False),
                    "aic": None, "log_likelihood": None, "parameter_count": None}
        result = {**smoother, "status": "descriptive_smoother", "fit_scope": "interior 0<C<1; separate empirical 0/1 atoms",
                  "scope_weight": 1.0, "endpoint_masses": {"p0": p0, "p1": p1}, "candidates": [candidate, smoother],
                  "reason": "Beta candidate failed descriptive screen; use boundary-reflected Gaussian KDE with Scott bandwidth. Smoothing only, not parametric acceptance; no KDE AIC claim."}
    return result


def fit_distribution(samples: np.ndarray, metric: str, model: str, model_metadata: dict | None, config: dict) -> dict:
    values = np.asarray(samples)
    if metric == "degree" and model == "er":
        params = {"trials": model_metadata["n"] - 1, "p": model_metadata["p"]}
        candidate = scored(values, "binomial_reference", params, 0)
        return {**candidate, "status": "model_reference", "reason": "Exact G(n,p) marginal degree reference using recorded p; not fitted to realized M.",
                "fit_scope": "all nodes", "scope_weight": 1.0, "candidates": [candidate]}
    if metric == "degree" and model == "ba":
        return power_tail_fit(values, config)
    if metric == "degree":
        return hurdle_counts(values, config, scope="all nodes; zero mass retained")
    if metric == "eccentricity":
        return eccentricity_fit(values, config)
    if metric == "clustering":
        return clustering_fit(values, config)
    if metric == "component_size":
        if len(values) == 1:
            return unavailable("One component: one observation and zero variance; fitting a shape is not meaningful.", "whole graph, one observation per component")
        return hurdle_counts(values[1:], config, scope="non-LCC components only; LCC remains an explicit empirical point", weight=(len(values) - 1) / len(values))
    raise ValueError(metric)


def curve_rows(fit: dict, frequencies: list[dict], bins: list[dict] | None = None) -> list[dict]:
    """Return plotted probabilities, not continuous densities, on saved empirical bins."""
    if fit["status"] == "N/A":
        return []
    if fit["method"] in ("zero_one_inflated_beta", "reflected_kde_mixture"):
        p = fit["parameters"]
        rows = []
        interior_freq = [row for row in frequencies if 0 < row["value"] < 1]
        for row in bins:
            if row["kind"] == "interior_bin" and fit["method"] == "reflected_kde_mixture":
                conditional = float(reflected_probability([row["left"]], [row["right"]],
                                    [f["value"] for f in interior_freq], [f["count"] for f in interior_freq], p["bandwidth"])[0])
            else:
                conditional = float(stats.beta.cdf(row["right"], p["a"], p["b"]) - stats.beta.cdf(row["left"], p["a"], p["b"])) if "a" in p else 0.0
            probability = (p["p0"] if row["kind"] == "zero_atom" else p["p1"] if row["kind"] == "one_atom"
                           else (1 - p["p0"] - p["p1"]) * conditional)
            rows.append({"model": fit["method"], "value": row["value"], "probability": float(probability), "selected": True, "kind": row["kind"]})
        return rows
    candidates = [{"method": fit["method"], "parameters": fit["parameters"]}]
    if "xmin_search" in fit and fit["method"] != "discrete_power_law_tail":
        candidates.append(next(candidate for candidate in fit["candidates"] if candidate["method"] == "discrete_power_law_tail"))
    rows = []
    for candidate in candidates:
        x = np.array([row["value"] for row in frequencies])
        if "xmin" in candidate["parameters"]:
            x = x[x >= candidate["parameters"]["xmin"]]
        probabilities = fit["scope_weight"] * candidate_pmf(candidate, x)
        rows += [{"model": candidate["method"], "value": float(value), "probability": float(probability),
                  "selected": candidate["method"] == fit["method"], "kind": "integer_value"}
                 for value, probability in zip(x, probabilities)]
    return rows
