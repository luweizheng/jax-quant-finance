"""The Euler sampling method for ito processes."""

from typing import Callable, List, Optional, Union

import numpy as np
import jax.numpy as jnp

from jax_quant_finance.math import random_sampler


def sample(
    dim: int,
    drift_fn: Callable[..., jnp.ndarray],
    volatility_fn: Callable[..., jnp.ndarray],
    times: Union[jnp.ndarray, np.ndarray, List[float]],
    time_step = None,
    num_time_steps = None,
    num_samples = 1,
    initial_state: Optional[Union[jnp.ndarray, np.ndarray, List[float]]] = None,
    random_type: Optional[random_sampler.RandomType] = None,
    seed: Optional[int] = None,
    precompute_normal_draws: bool = True,
    times_grid: Optional[Union[jnp.ndarray, np.ndarray]] = None,
    normal_draws: Optional[Union[jnp.ndarray, np.ndarray]] = None,
    validate_args: bool = False,
    tolerance: Optional[Union[jnp.ndarray, np.ndarray]] = None,
    dtype: Optional[jnp.dtype] = jnp.float64
    ) -> jnp.ndarray:
    """Returns a sample paths from the process using Euler method.

    For an Ito process,

    ```
        dX = a(t, X_t) dt + b(t, X_t) dW_t
        X(t=0) = x0
    ```
    with given drift `a` and volatility `b` functions Euler method generates a
    sequence {X_n} as

    ```
    X_{n+1} = X_n + a(t_n, X_n) dt + b(t_n, X_n) (N(0, t_{n+1}) - N(0, t_n)),
    X_0 = x0
    ```
    where `dt = t_{n+1} - t_n` and `N` is a sample from the Normal distribution.
    See [1] for details.

    #### Example
    Sampling from 2-dimensional Ito process of the form:

    ```none
    dX_1 = mu_1 * sqrt(t) dt + s11 * dW_1 + s12 * dW_2
    dX_2 = mu_2 * sqrt(t) dt + s21 * dW_1 + s22 * dW_2
    ```

    ```python
    import tensorflow as tf
    import tf_quant_finance as tff

    import numpy as np

    mu = np.array([0.2, 0.7])
    s = np.array([[0.3, 0.1], [0.1, 0.3]])
    num_samples = 10000
    dim = 2
    dtype = tf.float64

    # Define drift and volatility functions
    def drift_fn(t, x):
        return mu * tf.sqrt(t) * tf.ones([num_samples, dim], dtype=dtype)

    def vol_fn(t, x):
        return s * tf.ones([num_samples, dim, dim], dtype=dtype)

    # Set starting location
    x0 = np.array([0.1, -1.1])
    # Sample `num_samples` paths at specified `times` using Euler scheme.
    times = [0.1, 1.0, 2.0]
    paths = tff.models.euler_sampling.sample(
                dim=dim,
                drift_fn=drift_fn,
                volatility_fn=vol_fn,
                times=times,
                num_samples=num_samples,
                initial_state=x0,
                time_step=0.01,
                seed=42,
                dtype=dtype)
    # Expected: paths.shape = [10000, 3, 2]
    ```

    #### References
    [1]: Wikipedia. Euler-Maruyama method:
    https://en.wikipedia.org/wiki/Euler-Maruyama_method

    Args:
        dim: Python int greater than or equal to 1. The dimension of the Ito
        Process.
        drift_fn: A Python callable to compute the drift of the process. The
        callable should accept two real `Tensor` arguments of the same dtype.
        The first argument is the scalar time t, the second argument is the
        value of Ito process X - tensor of shape
        `batch_shape + [num_samples, dim]`. `batch_shape` is the shape of the
        independent stochastic processes being modelled and is inferred from the
        initial state `x0`.
        The result is value of drift a(t, X). The return value of the callable
        is a real `Tensor` of the same dtype as the input arguments and of shape
        `batch_shape + [num_samples, dim]`.
        volatility_fn: A Python callable to compute the volatility of the process.
        The callable should accept two real `Tensor` arguments of the same dtype
        and shape `times_shape`. The first argument is the scalar time t, the
        second argument is the value of Ito process X - tensor of shape
        `batch_shape + [num_samples, dim]`. The result is value of drift b(t, X).
        The return value of the callable is a real `Tensor` of the same dtype as
        the input arguments and of shape `batch_shape + [num_samples, dim, dim]`.
        times: Rank 1 `Tensor` of increasing positive real values. The times at
        which the path points are to be evaluated.
        time_step: An optional scalar real `Tensor` - maximal distance between
        points in grid in Euler schema.
        Either this or `num_time_steps` should be supplied.
        Default value: `None`.
        num_time_steps: An optional Scalar integer `Tensor` - a total number of time
        steps performed by the algorithm. The maximal distance betwen points in
        grid is bounded by `times[-1] / (num_time_steps - times.shape[0])`.
        Either this or `time_step` should be supplied.
        Default value: `None`.
        num_samples: Positive scalar `int`. The number of paths to draw.
        Default value: 1.
        initial_state: `Tensor` of shape broadcastable with
        `batch_shape + [num_samples, dim]`. The initial state of the process.
        `batch_shape` represents the shape of the independent batches of the
        stochastic process. Note that `batch_shape` is inferred from
        the `initial_state` and hence when sampling is requested for a batch of
        stochastic processes, the shape of `initial_state` should be at least
        `batch_shape + [1, 1]`.
        Default value: None which maps to a zero initial state.
        random_type: Enum value of `RandomType`. The type of (quasi)-random
        number generator to use to generate the paths.
        Default value: None which maps to the standard pseudo-random numbers.
        seed: Seed for the random number generator. The seed is
        only relevant if `random_type` is one of
        `[STATELESS, PSEUDO, HALTON_RANDOMIZED, PSEUDO_ANTITHETIC,
            STATELESS_ANTITHETIC]`. For `PSEUDO`, `PSEUDO_ANTITHETIC` and
        `HALTON_RANDOMIZED` the seed should be a Python integer. For
        `STATELESS` and  `STATELESS_ANTITHETIC `must be supplied as an integer
        `Tensor` of shape `[2]`.
        Default value: `None` which means no seed is set.
        swap_memory: A Python bool. Whether GPU-CPU memory swap is enabled for this
        op. See an equivalent flag in `tf.while_loop` documentation for more
        details. Useful when computing a gradient of the op since `tf.while_loop`
        is used to propagate stochastic process in time.
        Default value: True.
        skip: `int32` 0-d `Tensor`. The number of initial points of the Sobol or
        Halton sequence to skip. Used only when `random_type` is 'SOBOL',
        'HALTON', or 'HALTON_RANDOMIZED', otherwise ignored.
        Default value: `0`.
        precompute_normal_draws: Python bool. Indicates whether the noise increments
        `N(0, t_{n+1}) - N(0, t_n)` are precomputed. For `HALTON` and `SOBOL`
        random types the increments are always precomputed. While the resulting
        graph consumes more memory, the performance gains might be significant.
        Default value: `True`.
        times_grid: An optional rank 1 `Tensor` representing time discretization
        grid. If `times` are not on the grid, then the nearest points from the
        grid are used. When supplied, `num_time_steps` and `time_step` are
        ignored.
        Default value: `None`, which means that times grid is computed using
        `time_step` and `num_time_steps`.
        normal_draws: A `Tensor` of shape broadcastable with
        `batch_shape + [num_samples, num_time_points, dim]` and the same
        `dtype` as `times`. Represents random normal draws to compute increments
        `N(0, t_{n+1}) - N(0, t_n)`. When supplied, `num_samples` argument is
        ignored and the first dimensions of `normal_draws` is used instead.
        Default value: `None` which means that the draws are generated by the
        algorithm. By default normal_draws for each model in the batch are
        independent.
        watch_params: An optional list of zero-dimensional `Tensor`s of the same
        `dtype` as `initial_state`. If provided, specifies `Tensor`s with respect
        to which the differentiation of the sampling function will happen.
        A more efficient algorithm is used when `watch_params` are specified.
        Note the the function becomes differentiable onlhy wrt to these `Tensor`s
        and the `initial_state`. The gradient wrt any other `Tensor` is set to be
        zero.
        validate_args: Python `bool`. When `True` performs multiple checks:
        * That `times`  are increasing with the minimum increments of the
            specified tolerance.
        * If `normal_draws` are supplied, checks that `normal_draws.shape[1]` is
        equal to `num_time_steps` that is either supplied as an argument or
        computed from `time_step`.
        When `False` invalid dimension may silently render incorrect outputs.
        Default value: `False`.
        tolerance: A non-negative scalar `Tensor` specifying the minimum tolerance
        for discernible times on the time grid. Times that are closer than the
        tolerance are perceived to be the same.
        Default value: `None` which maps to `1-e6` if the for single precision
            `dtype` and `1e-10` for double precision `dtype`.
        dtype: `tf.Dtype`. If supplied the dtype for the input and output `Tensor`s.
        Default value: None which means that the dtype implied by `times` is
        used.
        name: Python string. The name to give this op.
        Default value: `None` which maps to `euler_sample`.

    Returns:
    A real `Tensor` of shape batch_shape_process + [num_samples, k, n] where `k`
        is the size of the `times`, `n` is the dimension of the process.

    Raises:
        ValueError:
        (a) When `times_grid` is not supplied, and neither `num_time_steps` nor
            `time_step` are supplied or if both are supplied.
        (b) If `normal_draws` is supplied and `dim` is mismatched.
        tf.errors.InvalidArgumentError: If `normal_draws` is supplied and
        `num_time_steps` is mismatched.
    """

    times = jnp.asarray(times, dtype=dtype)
    
    if tolerance is None:
        tolerance = 1e-10 if dtype == jnp.float64 else 1e-6
    tolerance = jnp.asarray(tolerance, dtype=dtype)
    # if validate_args:
    #   asserts.append(
    #       tf.assert_greater(
    #           times[1:], times[:-1] + tolerance,
    #           message='`times` increments should be greater '
    #                   'than tolerance {0}'.format(tolerance)))
    if initial_state is None:
        initial_state = jnp.zeros(dim, dtype=dtype)
    initial_state = jnp.asarray(initial_state, dtype=dtype)
    batch_shape = initial_state.shape[:-2]

    # compute the value of every element in times
    num_requested_times = times.shape[0]
    
    # Create a time grid for the Euler scheme.
    if num_time_steps is not None and time_step is not None:
      raise ValueError(
          'When `times_grid` is not supplied only one of either '
          '`num_time_steps` or `time_step` should be defined but not both.')
    if times_grid is None:
      if time_step is None:
        if num_time_steps is None:
          raise ValueError(
              'When `times_grid` is not supplied, either `num_time_steps` '
              'or `time_step` should be defined.')
        num_time_steps = jnp.asarray(num_time_steps, dtype=dtype)
        time_step = times[-1] / num_time_steps
      else:
        time_step = jnp.asarray(time_step, dtype=dtype)
    else:
        times_grid = jnp.asarray(times_grid, dtype=dtype)
        # if validate_args:
        #     asserts.append(
        #         tf.assert_greater(
        #             times_grid[1:], times_grid[:-1] + tolerance,
        #             message='`times_grid` increments should be greater '
        #                     'than tolerance {0}'.format(tolerance)))
    times, keep_mask, time_indices = utils.prepare_grid(
        times=times,
        time_step=time_step,
        num_time_steps=num_time_steps,
        times_grid=times_grid,
        tolerance=tolerance,
        dtype=dtype)

    if normal_draws is not None:
      normal_draws = tf.convert_to_tensor(normal_draws, dtype=dtype,
                                          name='normal_draws')
      # Shape [num_time_points] + batch_shape + [num_samples, dim]
      normal_draws_rank = normal_draws.shape.rank
      perm = tf.concat(
          [[normal_draws_rank-2], tf.range(normal_draws_rank-2),
           [normal_draws_rank-1]], axis=0)
      normal_draws = tf.transpose(normal_draws, perm=perm)
      num_samples = tf.shape(normal_draws)[-2]
      draws_dim = normal_draws.shape[-1]
      if dim != draws_dim:
        raise ValueError(
            '`dim` should be equal to `normal_draws.shape[2]` but are '
            '{0} and {1} respectively'.format(dim, draws_dim))
      if validate_args:
        draws_times = tff_utils.get_shape(normal_draws)[0]
        asserts.append(tf.assert_equal(
            draws_times, tf.shape(keep_mask)[0] - 1,
            message='`num_time_steps` should be equal to '
                    '`tf.shape(normal_draws)[1]`'))
    if validate_args:
      with tf.control_dependencies(asserts):
        times = tf.identity(times)
    if watch_params is not None:
      watch_params = [tf.convert_to_tensor(param, dtype=dtype)
                      for param in watch_params]
    return _sample(
        dim=dim,
        batch_shape=batch_shape,
        drift_fn=drift_fn,
        volatility_fn=volatility_fn,
        times=times,
        keep_mask=keep_mask,
        num_requested_times=num_requested_times,
        num_samples=num_samples,
        initial_state=initial_state,
        random_type=random_type,
        seed=seed,
        swap_memory=swap_memory,
        skip=skip,
        precompute_normal_draws=precompute_normal_draws,
        normal_draws=normal_draws,
        watch_params=watch_params,
        time_indices=time_indices,
        dtype=dtype)
